"""Sound Themes for NVDA: modern event-driven successor to two sound add-ons."""

from __future__ import annotations

import ctypes
import time
from pathlib import Path

import addonHandler
import config
import gui
import globalPluginHandler
import globalVars
import speech
import ui
import wx
from controlTypes import Role, State
from logHandler import log
from scriptHandler import script, getLastScriptRepeatCount
from utils.security import post_sessionLockStateChanged

from .audio import AudioEngine
from .browser import BrowseMonitor
from .browse_events import browse_cue
from .catalog import canonical_name, is_keyboard_event, is_typing_event
from .folderpacks import EmbeddedThemeStore
from .focus_policy import cue_for_focus
from .keyboard_state import KeyboardState
from .keyboard_catalog import event_for_virtual_key
from .keyboard_playback import cue_for_transition
from .modes import resolve_modes
from .updater import STARTUP_DELAY_MS, UpdateChecker

addonHandler.initTranslation()

SECTION = "soundThemes"
config.conf.spec[SECTION] = {
    "enabled": "boolean(default=true)",
    "navigation": "boolean(default=true)",
    "typing": "boolean(default=true)",
    "keyboard": "boolean(default=false)",
    "system": "boolean(default=true)",
    "pauseFeedback": "boolean(default=false)",
    "mouse": "boolean(default=false)",
    "hoverDelay": "integer(default=270)",
    "arrowNavSounds": "boolean(default=true)",
    "onlyEditable": "boolean(default=true)",
    # v0.16 before the hotfix played typing sounds on the desktop by default.
    # One-time migration restores typing-in-editors only for existing profiles;
    # the user can explicitly change the checkbox afterwards.
    "typingScopeMigrated": "boolean(default=false)",
    "sayRoles": "boolean(default=true)",
    "sayStates": "boolean(default=true)",
    "volume": "integer(default=65)",
    "theme": "string(default=builtin:voiceover)",
    "typingTheme": "string(default=builtin:classic-typewriter)",
    "keyboardTheme": "string(default=builtin:kat)",
    # Small preferences use NVDA's normal config, not another sound folder.
    "removedNavigationPresets": "string(default='')",
    "removedTypingPresets": "string(default='')",
    "removedKeyboardPresets": "string(default='')",
    "keyboardPlaybackModes": "string(default='')",
    "embeddedMigrationMap": "string(default='')",
    "checkForUpdates": "boolean(default=true)",
    "skippedUpdateVersion": "string(default='')",
}


def _output_device():
    try:
        return config.conf["audio"]["outputDevice"]
    except (KeyError, TypeError):
        return "Microsoft Sound Mapper"


def _pressed(vk: int) -> bool:
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except (AttributeError, OSError):
        return False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Sound Themes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._closed = False
        self._previous_role = None
        self._previous_app = None
        self._last_focus_cue = None
        self._last_switch_states = {}
        self._hover_obj = None
        self._hover_timer = None
        self._lock_timer = None
        self._subscriptions = []
        self._tools_item = None
        self._tools_menu = None
        self._settings_open = False
        self._update_timer = None
        self._updater = UpdateChecker()
        self._browse_monitor = BrowseMonitor(self)
        self.keys = KeyboardState()
        self._speech_original = None
        self._speech_wrapper = None
        self._role_speech_module = None
        # Typing Sounds is for entering text. Previously a fresh or upgraded
        # installation defaulted to playing on every typedCharacter event,
        # including Desktop/list quick search. Keyboard Sounds remains the
        # intentional mode for actual physical key sounds everywhere.
        if not config.conf[SECTION]["typingScopeMigrated"]:
            config.conf[SECTION]["onlyEditable"] = True
            config.conf[SECTION]["typingScopeMigrated"] = True
        # One package root for *all* sound packs. Never create the former
        # user-config/soundThemes/effects folder; it is read only for one-time
        # migration of older user's custom audio and preferences.
        asset_root = Path(__file__).resolve().parent / "effects"
        preferences = config.conf[SECTION]
        self.navigation_store = EmbeddedThemeStore(asset_root / "navigation", "navigation", preferences)
        self.typing_store = EmbeddedThemeStore(asset_root / "typing", "typing", preferences)
        self.keyboard_store = EmbeddedThemeStore(asset_root / "keyboard", "keyboard", preferences)
        if self.setting("keyboard"):
            # Guard settings migrated from older versions and manually edited configs.
            config.conf[SECTION]["navigation"] = False
            config.conf[SECTION]["typing"] = False
        legacy_root = Path(globalVars.appArgs.configPath) / "soundThemes"
        self._legacy_theme_ids = {}
        for store in (self.navigation_store, self.typing_store, self.keyboard_store):
            try:
                self._legacy_theme_ids[store.kind] = store.migrate_external(legacy_root / "effects")
            except (OSError, ValueError) as error:
                log.warning("Sound Themes: older sound pack migration skipped: %s", error)
        self._migrate_manifest_themes()
        self._migrate_old_user_themes(legacy_root / "themes")
        self.audio = AudioEngine(_output_device, log)
        self.reload_sounds()

        self._install_tools_menu()
        self._install_speech_filter()
        try:
            from speech.extensions import post_speechPaused
            self._register(post_speechPaused, self._speech_paused)
        except (ImportError, AttributeError):
            pass
        self._register(post_sessionLockStateChanged, self._session_state)
        try:
            from winAPI.secureDesktop import post_secureDesktopStateChange
            self._register(post_secureDesktopStateChange, self._secure_state)
        except (ImportError, AttributeError):
            pass
        try:
            from inputCore import decide_handleRawKey
            self._register(decide_handleRawKey, self._raw_key)
        except (ImportError, AttributeError):
            pass
        try:
            from logHandler import getOnErrorSoundRequested
            self._register(getOnErrorSoundRequested(), self._error_sound)
        except (ImportError, AttributeError):
            pass
        # vision.visionHandlerExtensionPoints is a MODULE defining the Action
        # container, not an instantiated post_browseModeMove event. The old
        # registration always failed on NVDA. Observe actual Browse Mode
        # cursor scripts instead, including single-letter navigation and
        # arrowing through web controls that never receive keyboard focus.
        try:
            self._browse_monitor.patch()
        except Exception as error:
            log.warning("Sound Themes: browse cursor monitoring unavailable: %s", error)
        try:
            from core import postNvdaStartup
            self._register(postNvdaStartup, self._startup)
        except (ImportError, AttributeError):
            pass
        if self.setting("checkForUpdates"):
            self._update_timer = wx.CallLater(STARTUP_DELAY_MS, self._updater.check, False)

    def _install_tools_menu(self):
        """One direct Tools entry; no nested NVDA Settings category."""
        try:
            tray = gui.mainFrame.sysTrayIcon
            self._tools_menu = tray.toolsMenu
            self._tools_item = self._tools_menu.Append(wx.ID_ANY, _("Sound Themes &settings..."))
            tray.Bind(wx.EVT_MENU, self._on_tools_settings, id=self._tools_item.GetId())
        except (AttributeError, RuntimeError) as error:
            log.warning("Sound Themes: Tools menu is unavailable: %s", error)

    def _on_tools_settings(self, evt):
        # Wait for the native menu to close before opening a modal dialog.
        try:
            wx.CallAfter(self._show_settings)
        except Exception:
            log.error("Sound Themes: could not schedule the settings window", exc_info=True)
            ui.message(_("Could not open Sound Themes settings. Please check the NVDA log."))

    def _show_settings(self):
        if self._closed or self._settings_open:
            return
        self._settings_open = True
        dialog = None
        popup_started = False
        try:
            from .settings import SoundSettingsDialog
            gui.mainFrame.prePopup()
            popup_started = True
            dialog = SoundSettingsDialog(gui.mainFrame, self)
            dialog.ShowModal()
        except Exception:
            # Unhandled wx errors previously made the Tools command appear to
            # do nothing. Always log the traceback and tell the user.
            log.error("Sound Themes: could not open the settings window", exc_info=True)
            try:
                wx.MessageBox(
                    _("Could not open Sound Themes settings. Please check the NVDA log."),
                    _("Sound Themes"),
                    wx.OK | wx.ICON_ERROR,
                    gui.mainFrame,
                )
            except Exception:
                ui.message(_("Could not open Sound Themes settings. Please check the NVDA log."))
        finally:
            if dialog is not None:
                try:
                    dialog.Destroy()
                except Exception:
                    log.error("Sound Themes: could not destroy the settings window", exc_info=True)
            if popup_started:
                try:
                    gui.mainFrame.postPopup()
                except Exception:
                    log.error("Sound Themes: could not restore the NVDA window", exc_info=True)
            self._settings_open = False

    def _register(self, point, callback):
        try:
            point.register(callback)
            self._subscriptions.append((point, callback))
        except Exception as error:
            log.warning("Sound Themes: event subscription unavailable: %s", error)

    def _migrate_old_user_themes(self, old_folder):
        try:
            import NVDAState
            if not NVDAState.shouldWriteToDisk:
                return
            for store in (self.navigation_store, self.typing_store):
                store.migrate_previous_themes(old_folder)
        except (ImportError, OSError, ValueError) as error:
            log.warning("Sound Themes: legacy theme migration skipped: %s", error)

    def _migrate_manifest_themes(self):
        try:
            import NVDAState
            if not NVDAState.shouldWriteToDisk:
                return
            for store in (self.navigation_store, self.typing_store):
                store.migrate_manifest_packs()
        except (ImportError, OSError, ValueError) as error:
            log.warning("Sound Themes: sound pack format upgrade skipped: %s", error)

    def setting(self, key: str):
        return config.conf[SECTION][key]

    def reload_sounds(self):
        names = self.navigation_store.themes()
        current = self.setting("theme")
        ids = [identifier for identifier, _ in names]
        if current not in ids:
            current = self._legacy_theme_ids.get("navigation", {}).get(current, current)
            if current.startswith("builtin:"):
                current = "user:" + current.split(":", 1)[1]
        if current not in ids:
            current = ids[0] if ids else ""
            config.conf[SECTION]["theme"] = current
        typing_names = self.typing_store.themes()
        typing_ids = [identifier for identifier, _ in typing_names]
        typing_theme = self.setting("typingTheme")
        if typing_theme not in typing_ids:
            typing_theme = self._legacy_theme_ids.get("typing", {}).get(typing_theme, typing_theme)
            if typing_theme.startswith("builtin:"):
                typing_theme = "user:" + typing_theme.split(":", 1)[1]
        if typing_theme not in typing_ids:
            typing_theme = typing_ids[0] if typing_ids else ""
            config.conf[SECTION]["typingTheme"] = typing_theme
        keyboard_names = self.keyboard_store.themes()
        keyboard_theme = self.setting("keyboardTheme")
        keyboard_ids = [identifier for identifier, _ in keyboard_names]
        if keyboard_theme not in keyboard_ids:
            keyboard_theme = self._legacy_theme_ids.get("keyboard", {}).get(keyboard_theme, keyboard_theme)
            if keyboard_theme.startswith("builtin:"):
                keyboard_theme = "user:" + keyboard_theme.split(":", 1)[1]
        if keyboard_theme not in keyboard_ids:
            keyboard_theme = keyboard_ids[0] if keyboard_ids else ""
            config.conf[SECTION]["keyboardTheme"] = keyboard_theme
        self._keyboard_playback_mode = (self.keyboard_store.playback_mode(keyboard_theme)
                                        if keyboard_theme else "press")
        self.audio.reload(self.navigation_store, current,
                          self.typing_store, typing_theme, self.setting("volume"),
                          self.keyboard_store, keyboard_theme)

    def play_event(self, event: str, min_gap: float = .05):
        if self._closed or not self.setting("enabled"):
            return
        if event.startswith("system.") and not self.setting("system"):
            return
        if is_keyboard_event(event) and not self.setting("keyboard"):
            return
        if is_typing_event(event) and not self.setting("typing"):
            return
        if not (event.startswith("system.") or is_typing_event(event) or is_keyboard_event(event)):
            if not self.setting("navigation"):
                return
        self.audio.play(event, min_gap)

    def _session_state(self, isNowLocked: bool):
        if isNowLocked:
            self.play_event("system.lock", 0)
            if self._lock_timer is not None:
                self._lock_timer.Stop()
            self._lock_timer = wx.CallLater(180, self.play_event, "system.lockscreen", 0)
        else:
            if self._lock_timer is not None:
                self._lock_timer.Stop()
            self.play_event("system.unlock", 0)

    def _secure_state(self, *args, **kwargs):
        """Track secure desktop separately from Windows session lock/unlock."""
        state = next((kwargs[key] for key in ("isSecureDesktop", "isSecure", "secure")
                      if key in kwargs), None)
        if state is None and args and isinstance(args[0], bool):
            state = args[0]
        if state is not None:
            self.play_event("system.secure_enter" if state else "system.secure_exit", 0)

    def _raw_key(self, vkCode, scanCode=None, extended=False, pressed=True, **kwargs):
        """Observe NVDA's existing keyboard hook; never swallow system input."""
        try:
            if kwargs.get("injected", False):
                return True
            # De-duplicate generic Shift/Ctrl/Alt and their left/right VKs.
            # One physical keydown must play ONE assigned sample, even when
            # a keyboard driver reports both aliases to NVDA.
            changed, physical_vk = self.keys.transition_physical(
                vkCode, scanCode, extended, pressed,
            )
            if changed and not self._closed and self.setting("keyboard"):
                event = event_for_virtual_key(vkCode, scanCode, extended)
                if physical_vk == 0x09 and self.keys.is_pressed(0x10):
                    event = "keyboard.shift_tab"
                # The audio engine only queues cached bytes. Scheduling via
                # wx.CallAfter needlessly delays fast keyboard feedback.
                cue = cue_for_transition(event, pressed, changed, self._keyboard_playback_mode)
                if cue is not None:
                    # The pressed-key state already filters auto-repeat;
                    # a further 18 ms audio throttle clips genuine fast taps.
                    # Never wait, sleep or decode audio on NVDA's key hook.
                    self.play_event(cue, 0)
            elif changed and pressed and not self._closed and self.setting("typing"):
                # NVDA doesn't reliably emit typedCharacter for Return,
                # Backspace, Delete or Space in every editable application.
                # Listen to the existing raw hook only for these four keys
                # and only when an actual editable field has focus.
                special = {0x0D: "key.enter", 0x08: "key.backspace",
                           0x2E: "key.backspace", 0x20: "key.space"}.get(physical_vk)
                if special:
                    obj = self._focused_editable()
                    if obj is not None:
                        if State.PROTECTED in (getattr(obj, "states", ()) or ()):
                            special = "key.protected"
                        self.keys.note_typing_special(special)
                        self.play_event(special, .018)
        except Exception:
            pass
        return True

    def _typing_allowed(self, obj=None):
        if not self.setting("onlyEditable"):
            return True
        return self._focused_editable(obj) is not None

    def _focused_editable(self, obj=None):
        """Only real editable controls may receive raw typing key sounds."""
        if obj is None:
            try:
                import api
                obj = api.getFocusObject()
            except Exception:
                return None
        states = getattr(obj, "states", ()) or ()
        if (State.READONLY not in states and
                (State.EDITABLE in states or getattr(obj, "role", None) == Role.EDITABLETEXT)):
            return obj
        return None

    def _error_sound(self, *args, **kwargs):
        self.play_event("system.error", 0)

    def _speech_paused(self, switch: bool):
        """Opt-in pause cue, never for the ordinary Shift-to-pause gesture.

        NVDA emits post_speechPaused when Shift pauses speech. This is a
        system callback, not a keyboard sound, so the Navigation switch does
        not affect it. Keep it independent and silent by default.
        """
        if (switch and self.setting("pauseFeedback") and
                not self.keys.shift_recent() and not _pressed(0x10)):
            self.play_event("system.paused_feedback", 0)

    def _startup(self, *args, **kwargs):
        self.play_event("system.ready" if self.audio.has_sound("system.ready")
                        else "system.start", 0)

    def browse_moved(self, info, hint=None, root=None):
        """Play the actual web element role when the virtual caret moves."""
        self.play_event(browse_cue(info, hint=hint, root=root), .035)

    def _install_speech_filter(self):
        # Preserve navSounds' option without hijacking the legacy
        # speech.getSpeechTextForProperties API removed in recent NVDA.
        source = getattr(speech, "speech", None)
        if source is None:
            return
        original = getattr(source, "getPropertiesSpeech", None)
        if not callable(original):
            return

        def filtered(*args, **kwargs):
            if not self._closed and self.setting("enabled"):
                kwargs = dict(kwargs)
                role = kwargs.get("role")
                if role is not None and not self.setting("sayRoles"):
                    if self.audio.has_exact_sound("role." + canonical_name(role)):
                        kwargs.pop("role", None)
                states = kwargs.get("states")
                if states and not self.setting("sayStates"):
                    muted = {state for state in states
                             if self.audio.has_exact_sound("state." + canonical_name(state))}
                    if muted:
                        kwargs["states"] = (states - muted if isinstance(states, set)
                                            else [state for state in states if state not in muted])
            return original(*args, **kwargs)

        self._role_speech_module = source
        self._speech_original = original
        self._speech_wrapper = filtered
        source.getPropertiesSpeech = filtered

    def _play_role_or_state(self, obj):
        self.play_event(cue_for_focus(getattr(obj, "role", None),
                                      getattr(obj, "states", ()),
                                      self.audio.has_exact_sound))

    def _play_focus_once(self, obj):
        """One role cue per movement, even if focus and selection both fire."""
        now = time.monotonic()
        fingerprint = (getattr(obj, "windowHandle", None),
                       getattr(obj, "IAccessibleChildID", None),
                       canonical_name(getattr(obj, "role", None)),
                       getattr(obj, "name", None))
        if self._last_focus_cue is not None:
            previous, timestamp = self._last_focus_cue
            if previous == fingerprint and now - timestamp < .075:
                return
        self._last_focus_cue = (fingerprint, now)
        if (not getattr(obj, "name", None)
                and getattr(obj, "role", None) in (None, Role.UNKNOWN)):
            self.play_event("nav.empty")
            return
        self._play_role_or_state(obj)

    def _key_context(self):
        # Context is used ONLY to identify activation/scroll after focus moved.
        # A pressed key itself NEVER plays a navigation sound.
        down = lambda key: self.keys.is_pressed(key) or _pressed(key)
        if down(0x09):
            return "key.shift_tab" if down(0x10) else "key.tab"
        if down(0x0d):
            return "key.enter"
        if down(0x20):
            return "key.space"
        if down(0x21) or down(0x22):
            return "key.page"
        if down(0x24) or down(0x23):
            return "key.home_end"
        for vk, name in ((0x26, "up"), (0x28, "down"), (0x25, "left"), (0x27, "right")):
            if down(vk):
                return f"key.{name}"
        return None

    def event_gainFocus(self, obj, nextHandler):
        try:
            module = getattr(obj, "appModule", None)
            app = getattr(module, "appName", None)
            if app and self._previous_app != app:
                if self._previous_app is not None:
                    # An application transition is not a tree collapse or
                    # an activation. Emit only its most specific cue.
                    if app == "explorer":
                        self.play_event("nav.open")
                    elif self._previous_app == "explorer":
                        self.play_event("nav.close")
                    else:
                        self.play_event("system.app_switch")
                self._previous_app = app
            if (self._previous_role == Role.EDITABLETEXT
                    and getattr(obj, "role", None) != Role.EDITABLETEXT):
                self.play_event("nav.edit_exit")
            key = self._key_context()
            if key == "key.page":
                self.play_event("nav.scroll")
            self._play_focus_once(obj)
            self._previous_role = getattr(obj, "role", None)
        except Exception as error:
            log.debugWarning("Sound Themes focus handler: %s", error)
        finally:
            nextHandler()

    def event_typedCharacter(self, obj, nextHandler, ch):
        try:
            role = getattr(obj, "role", None)
            if self.setting("typing") and role in (getattr(Role, "LIST", None), Role.TREEVIEW) and any(
                    _pressed(vk) for vk in (0x25, 0x26, 0x27, 0x28)):
                # Preserve the original ScreenReaderSounds invalid-list cue.
                self.play_event("key.invalid")
            if role in (Role.BUTTON, Role.CHECKBOX, getattr(Role, "TOGGLEBUTTON", None),
                        Role.MENUITEM, Role.LISTITEM) and (_pressed(0x20) or _pressed(0x0d)):
                self.play_event("nav.activate")
            states = getattr(obj, "states", ()) or ()
            if self._typing_allowed(obj):
                if State.PROTECTED in states:
                    event = "key.protected"
                elif ch == " ":
                    event = "key.space"
                elif ch in ("\b", "\x7f"):
                    event = "key.backspace"
                elif ch in ("\r", "\n"):
                    event = "key.enter"
                else:
                    event = "key.character"
                if not self.keys.consume_typing_special(event):
                    self.play_event(event, .035)
        except Exception:
            pass
        finally:
            nextHandler()

    def event_mouseMove(self, obj, nextHandler, x, y):
        try:
            ignored = {getattr(Role, name, None) for name in
                       ("DOCUMENT", "WINDOW", "PANE", "APPLICATION", "UNKNOWN")}
            if not self.setting("mouse") or getattr(obj, "role", None) in ignored:
                self._hover_obj = None
                if self._hover_timer is not None:
                    self._hover_timer.Stop()
                    self._hover_timer = None
            elif obj != self._hover_obj:
                self._hover_obj = obj
                if self._hover_timer is not None:
                    self._hover_timer.Stop()
                self._hover_timer = wx.CallLater(self.setting("hoverDelay"), self._hover, obj)
        finally:
            nextHandler()

    def _hover(self, obj):
        if self._hover_obj is obj and not self._closed:
            if getattr(obj, "role", None) is None:
                self.play_event("nav.mouse")
            else:
                self._play_role_or_state(obj)

    def _event(self, event, obj, nextHandler):
        try:
            self.play_event(event)
        finally:
            nextHandler()

    def event_foreground(self, obj, nextHandler):
        try:
            self.play_event("system.window")
            self.play_event("object.foreground")
        finally:
            nextHandler()

    def event_focusEntered(self, obj, nextHandler):
        self._event("object.focus_entered", obj, nextHandler)

    def event_loseFocus(self, obj, nextHandler):
        self._event("object.focus_lost", obj, nextHandler)

    def event_nameChange(self, obj, nextHandler):
        self._event("object.name", obj, nextHandler)

    def event_descriptionChange(self, obj, nextHandler):
        self._event("object.description", obj, nextHandler)

    def event_valueChange(self, obj, nextHandler):
        self._event("object.value", obj, nextHandler)

    def event_stateChange(self, obj, nextHandler):
        try:
            states = getattr(obj, "states", ()) or ()
            if getattr(obj, "role", None) == getattr(Role, "SWITCH", None):
                key = (getattr(obj, "windowHandle", None),
                       getattr(obj, "IAccessibleChildID", None), getattr(obj, "name", None))
                on = getattr(State, "ON", None) in states
                old = self._last_switch_states.get(key)
                self._last_switch_states[key] = on
                if len(self._last_switch_states) > 128:
                    self._last_switch_states.pop(next(iter(self._last_switch_states)))
                if old is None or old != on:
                    self.play_event("state.on" if on else "state.off")
            elif State.EXPANDED in states:
                self.play_event("nav.expand")
            elif State.COLLAPSED in states:
                self.play_event("nav.collapse")
            elif State.PRESSED in states or State.CHECKED in states:
                self.play_event("nav.activate")
            else:
                self.play_event("object.state")
        finally:
            nextHandler()

    def event_caret(self, obj, nextHandler):
        try:
            # A caret callback also follows each typed character and can be
            # emitted for background text refreshes. Neither should create a
            # second, unexplained navigation sound after the typing sample.
            if self.setting("arrowNavSounds") and (
                    self.keys.navigation_recent()
                    or self._key_context() in ("key.up", "key.down", "key.left", "key.right",
                                               "key.page", "key.home_end")):
                self.play_event("nav.caret")
        finally:
            nextHandler()

    def event_selection(self, obj, nextHandler):
        try:
            # Explorer often announces list selection independently of focus.
            # Treat item selection as navigation, using its real role sound.
            role = canonical_name(getattr(obj, "role", None))
            if role not in ("listitem", "treeviewitem", "dataitem", "tablecell", "cell", "row"):
                try:
                    import api
                    focused = api.getFocusObject()
                    focused_role = canonical_name(getattr(focused, "role", None))
                    focused_app = getattr(getattr(focused, "appModule", None), "appName", None)
                    if focused_app == "explorer" and focused_role in (
                            "listitem", "treeviewitem", "dataitem", "tablecell", "cell", "row"):
                        obj = focused
                        role = focused_role
                except Exception:
                    pass
            if role in ("listitem", "treeviewitem", "dataitem", "tablecell", "cell", "row"):
                self._play_focus_once(obj)
            else:
                self.play_event("nav.tick" if self.audio.has_sound("nav.tick") else "nav.selection")
        finally:
            nextHandler()

    def event_alert(self, obj, nextHandler):
        self._event("system.alert", obj, nextHandler)

    def event_notification(self, obj, nextHandler):
        self._event("system.notification", obj, nextHandler)

    def event_show(self, obj, nextHandler):
        self._event("object.show", obj, nextHandler)

    def event_hide(self, obj, nextHandler):
        self._event("object.hide", obj, nextHandler)

    def event_documentLoadComplete(self, obj, nextHandler):
        try:
            self.play_event("system.complete")
            self.play_event("object.document")
        finally:
            nextHandler()

    def event_textChange(self, obj, nextHandler):
        self._event("object.text", obj, nextHandler)

    def event_liveRegionChange(self, obj, nextHandler):
        self._event("object.live", obj, nextHandler)

    def event_locationChange(self, obj, nextHandler):
        self._event("object.location", obj, nextHandler)

    @script(description=_("Toggle navigation sounds; press twice to toggle typing sounds"), gesture="kb:NVDA+alt+n")
    def script_toggleNavigation(self, gesture):
        option = "typing" if getLastScriptRepeatCount() else "navigation"
        config.conf[SECTION][option] = not self.setting(option)
        nav, typing, keyboard = resolve_modes(self.setting("navigation"), self.setting("typing"),
                                               self.setting("keyboard"), option)
        config.conf[SECTION]["navigation"] = nav
        config.conf[SECTION]["typing"] = typing
        config.conf[SECTION]["keyboard"] = keyboard
        ui.message(_("%s sounds %s") % (option, _("on") if self.setting(option) else _("off")))

    @script(description=_("Toggle all sound themes"), gesture="kb:NVDA+alt+o")
    def script_toggleAll(self, gesture):
        config.conf[SECTION]["enabled"] = not self.setting("enabled")
        ui.message(_("Sound Themes %s") % (_("on") if self.setting("enabled") else _("off")))

    def _change_theme(self, step: int):
        themes = self.navigation_store.themes()
        if not themes:
            ui.message(_("No sound themes found"))
            return
        ids = [identifier for identifier, _ in themes]
        old = self.setting("theme")
        pos = ids.index(old) if old in ids else 0
        new_id, label = themes[(pos + step) % len(themes)]
        config.conf[SECTION]["theme"] = new_id
        self.reload_sounds()
        ui.message(_("Sound theme: %s") % label)

    @script(description=_("Previous sound theme"), gesture="kb:NVDA+alt+z")
    def script_previousTheme(self, gesture):
        self._change_theme(-1)

    @script(description=_("Next sound theme"), gesture="kb:NVDA+alt+x")
    def script_nextTheme(self, gesture):
        self._change_theme(1)

    def terminate(self):
        self.play_event("system.stop", 0)
        self._closed = True
        self._updater.terminate()
        if self._update_timer is not None:
            self._update_timer.Stop()
        if self._tools_item is not None and self._tools_menu is not None:
            try:
                tray = gui.mainFrame.sysTrayIcon
                tray.Unbind(wx.EVT_MENU, id=self._tools_item.GetId())
                self._tools_menu.Delete(self._tools_item.GetId())
            except (AttributeError, RuntimeError):
                pass
            self._tools_item = None
        if self._hover_timer is not None:
            self._hover_timer.Stop()
        if self._lock_timer is not None:
            self._lock_timer.Stop()
        for point, callback in reversed(self._subscriptions):
            try:
                point.unregister(callback)
            except Exception:
                pass
        self._browse_monitor.terminate()
        self.keys.clear()
        self._last_switch_states.clear()
        if self._role_speech_module is not None:
            if getattr(self._role_speech_module, "getPropertiesSpeech", None) is self._speech_wrapper:
                self._role_speech_module.getPropertiesSpeech = self._speech_original
        self.audio.close()
        super().terminate()
