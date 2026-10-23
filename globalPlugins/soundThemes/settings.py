"""Keyboard and screen-reader friendly wx dialogs for managing sound themes."""

from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile
import os

import wx
import addonHandler
import languageHandler
import ui
from controlTypes import Role, State
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel

from .catalog import all_events, event_description
from .keyboard_catalog import all_keyboard_events, event_for_virtual_key, name_for_event
from .modes import resolve_modes

addonHandler.initTranslation()


def explain_error(parent, error):
    wx.MessageBox(str(error), _("Sound Themes"), wx.OK | wx.ICON_ERROR, parent)


def ask_name(parent, title: str, initial: str = "") -> str | None:
    dialog = wx.TextEntryDialog(parent, _("Theme name:"), title, value=initial)
    try:
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue().strip()
            if name:
                return name
    finally:
        dialog.Destroy()
    return None


def preview_selected_theme(plugin, store, identifier):
    """Audition a pack without activating it or blocking the wx event loop."""
    if not identifier:
        return
    try:
        path = store.preview_sound(identifier)
        if path is not None:
            plugin.audio.preview_file(path, plugin.setting("volume"))
    except (ValueError, OSError, KeyError):
        # An empty/unreadable theme should not interrupt keyboard navigation.
        pass


class SoundSettingsPanel(SettingsPanel):
    plugin = None
    title = _("Sound Themes")

    def makeSettings(self, sizer):
        self.helper = guiHelper.BoxSizerHelper(self, sizer=sizer)
        plugin = self.plugin
        navigation = plugin.navigation_store.themes()
        typing = plugin.typing_store.themes()
        keyboard = plugin.keyboard_store.themes()
        self.nav_ids = [theme_id for theme_id, _ in navigation]
        self.typing_ids = [theme_id for theme_id, _ in typing]
        self.keyboard_ids = [theme_id for theme_id, _ in keyboard]
        self.helper.addItem(wx.StaticText(self, label=_("Active sound &theme:")))
        self.theme = self.helper.addItem(wx.Choice(self, choices=[name for _, name in navigation]))
        self.theme.SetName(_("Active sound theme"))
        chosen = plugin.setting("theme")
        if chosen in self.nav_ids:
            self.theme.SetSelection(self.nav_ids.index(chosen))
        self.helper.addItem(wx.StaticText(self, label=_("&Typing sound theme (can be different):")))
        self.typing_theme = self.helper.addItem(wx.Choice(self, choices=[name for _, name in typing]))
        self.typing_theme.SetName(_("Typing sound theme"))
        typing_chosen = plugin.setting("typingTheme")
        if typing_chosen in self.typing_ids:
            self.typing_theme.SetSelection(self.typing_ids.index(typing_chosen))
        self.helper.addItem(wx.StaticText(self, label=_("&Keyboard sound theme (individual keys):")))
        self.keyboard_theme = self.helper.addItem(wx.Choice(self, choices=[name for _, name in keyboard]))
        self.keyboard_theme.SetName(_("Keyboard sound theme"))
        keyboard_chosen = plugin.setting("keyboardTheme")
        if keyboard_chosen in self.keyboard_ids:
            self.keyboard_theme.SetSelection(self.keyboard_ids.index(keyboard_chosen))
        self.theme.Bind(wx.EVT_CHOICE, lambda evt: self.preview_setting_theme(
            self.theme, self.nav_ids, plugin.navigation_store))
        self.typing_theme.Bind(wx.EVT_CHOICE, lambda evt: self.preview_setting_theme(
            self.typing_theme, self.typing_ids, plugin.typing_store))
        self.keyboard_theme.Bind(wx.EVT_CHOICE, lambda evt: self.preview_setting_theme(
            self.keyboard_theme, self.keyboard_ids, plugin.keyboard_store))

        self.enabled = self._check(_("&Enable sound effects"), "enabled")
        self.navigation = self._check(_("Play &navigation, role and state sounds"), "navigation")
        self.typing = self._check(_("Play &typing sounds"), "typing")
        self.keyboard = self._check(_("Play &Keyboard Sounds for individual keys (disables navigation and typing)"), "keyboard")
        self.navigation.Bind(wx.EVT_CHECKBOX, lambda evt: self.on_mode_change("navigation"))
        self.typing.Bind(wx.EVT_CHECKBOX, lambda evt: self.on_mode_change("typing"))
        self.keyboard.Bind(wx.EVT_CHECKBOX, lambda evt: self.on_mode_change("keyboard"))
        self.system = self._check(_("Play &system sounds, including lock/unlock"), "system")
        self.pauseFeedback = self._check(
            _("Play speech-pause feedback (except when pressing Shift; off by default)"),
            "pauseFeedback",
        )
        self.mouse = self._check(_("Play sounds on mouse &hover"), "mouse")
        self.mouse.Bind(wx.EVT_CHECKBOX, self.on_mouse)
        self.onlyEditable = self._check(_("Only play typing sounds in &editable fields"), "onlyEditable")
        self.arrowNavSounds = self._check(_("Play arrow &navigation sounds"), "arrowNavSounds")
        self.sayRoles = self._check(_("Speak element &roles"), "sayRoles")
        self.sayStates = self._check(_("Speak element &states"), "sayStates")

        self.helper.addItem(wx.StaticText(self, label=_("Mouse hover &delay (milliseconds):")))
        self.delay = self.helper.addItem(wx.SpinCtrl(self, min=50, max=2000))
        self.delay.SetName(_("Mouse hover delay"))
        self.delay.SetValue(plugin.setting("hoverDelay"))
        self.delay.Enable(self.mouse.GetValue())

        self.helper.addItem(wx.StaticText(self, label=_("Effect &volume (0 to 100):")))
        self.volume = self.helper.addItem(wx.Slider(self, minValue=0, maxValue=100, value=plugin.setting("volume")))
        self.volume.SetName(_("Effect volume"))

        manager = self.helper.addItem(wx.Button(self, label=_("&Manage sound themes...")))
        manager.Bind(wx.EVT_BUTTON, self.manage)
        open_folders = self.helper.addItem(wx.Button(self, label=_("&Open sound folders")))
        open_folders.Bind(wx.EVT_BUTTON, self.on_open_folder)

    def _check(self, label, key):
        cb = self.helper.addItem(wx.CheckBox(self, label=label))
        cb.SetValue(self.plugin.setting(key))
        return cb

    def preview_setting_theme(self, control, identifiers, store):
        index = control.GetSelection()
        if 0 <= index < len(identifiers):
            preview_selected_theme(self.plugin, store, identifiers[index])

    def on_mouse(self, evt):
        self.delay.Enable(self.mouse.GetValue())

    def on_mode_change(self, changed):
        values = resolve_modes(self.navigation.GetValue(), self.typing.GetValue(),
                               self.keyboard.GetValue(), changed)
        for control, value in zip((self.navigation, self.typing, self.keyboard), values):
            control.SetValue(value)

    def on_open_folder(self, evt):
        try:
            for store in (self.plugin.navigation_store, self.plugin.typing_store,
                          self.plugin.keyboard_store):
                store.writable.mkdir(parents=True, exist_ok=True)
            directory = self.plugin.navigation_store.writable.parent
            os.startfile(str(directory))
        except (OSError, AttributeError) as error:
            explain_error(self, error)

    def manage(self, evt):
        dialog = ThemeManager(self, self.plugin)
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()
        navigation = self.plugin.navigation_store.themes()
        typing = self.plugin.typing_store.themes()
        keyboard = self.plugin.keyboard_store.themes()
        self.nav_ids = [theme_id for theme_id, _ in navigation]
        self.typing_ids = [theme_id for theme_id, _ in typing]
        self.keyboard_ids = [theme_id for theme_id, _ in keyboard]
        self.theme.Set([name for _, name in navigation])
        self.typing_theme.Set([name for _, name in typing])
        self.keyboard_theme.Set([name for _, name in keyboard])
        chosen = self.plugin.setting("theme")
        if chosen in self.nav_ids:
            self.theme.SetSelection(self.nav_ids.index(chosen))
        typing_chosen = self.plugin.setting("typingTheme")
        if typing_chosen in self.typing_ids:
            self.typing_theme.SetSelection(self.typing_ids.index(typing_chosen))
        keyboard_chosen = self.plugin.setting("keyboardTheme")
        if keyboard_chosen in self.keyboard_ids:
            self.keyboard_theme.SetSelection(self.keyboard_ids.index(keyboard_chosen))

    def onSave(self):
        import config
        from . import SECTION
        selected = self.theme.GetSelection()
        if 0 <= selected < len(self.nav_ids):
            config.conf[SECTION]["theme"] = self.nav_ids[selected]
        typing_selected = self.typing_theme.GetSelection()
        if 0 <= typing_selected < len(self.typing_ids):
            config.conf[SECTION]["typingTheme"] = self.typing_ids[typing_selected]
        keyboard_selected = self.keyboard_theme.GetSelection()
        if 0 <= keyboard_selected < len(self.keyboard_ids):
            config.conf[SECTION]["keyboardTheme"] = self.keyboard_ids[keyboard_selected]
        self.on_mode_change("keyboard" if self.keyboard.GetValue() else "")
        for key in ("enabled", "navigation", "typing", "system", "pauseFeedback", "mouse", "onlyEditable",
                    "arrowNavSounds", "sayRoles", "sayStates", "keyboard"):
            config.conf[SECTION][key] = getattr(self, key).GetValue()
        config.conf[SECTION]["hoverDelay"] = self.delay.GetValue()
        config.conf[SECTION]["volume"] = self.volume.GetValue()
        self.plugin.reload_sounds()


class ThemeManager(wx.Dialog):
    def __init__(self, parent, plugin):
        super().__init__(parent, title=_("Manage sound themes"), size=(750, 650),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main = wx.BoxSizer(wx.VERTICAL)
        notebook = wx.Notebook(self)
        for kind, label, store in (
            ("navigation", _("Navigation"), plugin.navigation_store),
            ("typing", _("Typing"), plugin.typing_store),
            ("keyboard", _("Keyboard Sounds"), plugin.keyboard_store),
        ):
            page = ThemeManagerPage(notebook, plugin, store, kind)
            notebook.AddPage(page, label)
        main.Add(notebook, 1, wx.ALL | wx.EXPAND, 8)
        close = wx.Button(self, wx.ID_CLOSE, _("&Close"))
        close.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CLOSE))
        main.Add(close, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        self.SetSizer(main)


class ThemeManagerPage(wx.Panel):
    def __init__(self, parent, plugin, store, kind):
        super().__init__(parent)
        self.plugin = plugin
        self.store = store
        self.kind = kind
        self.setting_key = {"navigation": "theme", "typing": "typingTheme",
                            "keyboard": "keyboardTheme"}[kind]
        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(wx.StaticText(self, label=_("Sound themes (built-in themes are read-only):")),
                 0, wx.ALL, 8)
        self.theme_list = wx.ListBox(self, style=wx.LB_SINGLE)
        self.theme_list.SetName(_("Available sound themes"))
        self.theme_list.Bind(wx.EVT_LISTBOX, self.on_theme_selection)
        main.Add(self.theme_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        buttons = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        actions = (
            (_("&Create / copy selected..."), self.create),
            (_("&Edit sounds..."), self.edit),
            (_("Re&name..."), self.rename),
            (_("&Delete..."), self.delete),
            (_("Import theme &ZIP..."), self.import_zip),
            (_("Import old sounds &folder..."), self.import_legacy),
            (_("E&xport theme ZIP..."), self.export),
            (_("&Use this theme"), self.activate),
        )
        for title, handler in actions:
            button = wx.Button(self, label=title)
            button.Bind(wx.EVT_BUTTON, handler)
            buttons.Add(button, 0, wx.EXPAND)
        buttons.AddGrowableCol(0, 1)
        buttons.AddGrowableCol(1, 1)
        main.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        self.SetSizer(main)
        self.refresh(self.plugin.setting(self.setting_key))

    def refresh(self, select_id=None):
        self.choices = self.store.themes()
        # A native list can jump to "Cherry" with C only if the label STARTS
        # with Cherry. Keep the source (builtin/user) in the opaque ID instead.
        self.theme_list.Set([name for _, name in self.choices])
        ids = [identifier for identifier, _ in self.choices]
        if select_id in ids:
            self.theme_list.SetSelection(ids.index(select_id))
        elif ids:
            self.theme_list.SetSelection(0)

    def on_theme_selection(self, evt):
        index = self.theme_list.GetSelection()
        if 0 <= index < len(self.choices):
            preview_selected_theme(self.plugin, self.store, self.choices[index][0])

    def selected(self):
        index = self.theme_list.GetSelection()
        if index < 0:
            raise ValueError(_("Select a sound theme first"))
        return self.choices[index][0]

    def _act(self, action):
        try:
            return action()
        except (ValueError, OSError, PermissionError, KeyError, FileExistsError, BadZipFile) as error:
            explain_error(self, error)
            return None

    def create(self, evt):
        name = ask_name(self, _("Create sound theme"))
        if name:
            base = self.selected() if self.choices else None
            new = self._act(lambda: self.store.create(name, base))
            if new:
                self.refresh(new)

    def edit(self, evt):
        identifier = self._act(self.selected)
        if not identifier:
            return
        if identifier.startswith("builtin:"):
            name = ask_name(self, _("Copy built-in theme to edit"))
            if not name:
                return
            identifier = self._act(lambda: self.store.create(name, identifier))
            if not identifier:
                return
            self.refresh(identifier)
        editor = ThemeEditor(self, self.plugin, self.store, identifier)
        try:
            editor.ShowModal()
        finally:
            editor.Destroy()
        self.plugin.reload_sounds()

    def rename(self, evt):
        identifier = self._act(self.selected)
        if not identifier:
            return
        if identifier.startswith("builtin:"):
            explain_error(self, _("Built-in sound packs cannot be renamed"))
            return
        name = ask_name(self, _("Rename sound theme"), self.store.load(identifier)["name"])
        if name:
            changed = self._act(lambda: self.store.rename(identifier, name))
            if changed:
                if self.plugin.setting(self.setting_key) == identifier:
                    import config
                    from . import SECTION
                    config.conf[SECTION][self.setting_key] = changed
                self.plugin.reload_sounds()
                self.refresh(changed)

    def delete(self, evt):
        identifier = self._act(self.selected)
        if not identifier:
            return
        if identifier.startswith("builtin:"):
            explain_error(self, _("Built-in themes cannot be removed"))
            return
        if wx.MessageBox(_("Delete this theme permanently?"), _("Confirm deletion"),
                         wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING, self) == wx.YES:
            self._act(lambda: self.store.delete(identifier))
            if self.plugin.setting(self.setting_key) == identifier:
                import config
                from . import SECTION
                remaining = self.store.themes()
                config.conf[SECTION][self.setting_key] = remaining[0][0] if remaining else ""
                self.plugin.reload_sounds()
            self.refresh(self.plugin.setting(self.setting_key))

    def import_zip(self, evt):
        with wx.FileDialog(self, _("Import theme ZIP"), wildcard="ZIP files (*.zip)|*.zip",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            source = Path(dialog.GetPath())
        name = ask_name(self, _("Name imported theme"), source.stem)
        if name:
            new = self._act(lambda: self.store.import_zip(source, name))
            if new:
                self.refresh(new)

    def import_legacy(self, evt):
        with wx.DirDialog(self, _("Choose a folder with old WAV sound files")) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            folder = Path(dialog.GetPath())
        name = ask_name(self, _("Name imported theme"), folder.name)
        if name:
            new = self._act(lambda: self.store.import_legacy_folder(folder, name, Role, State))
            if new:
                self.refresh(new)

    def export(self, evt):
        identifier = self._act(self.selected)
        if not identifier:
            return
        with wx.FileDialog(self, _("Export sound theme"), wildcard="ZIP files (*.zip)|*.zip",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=identifier.split(":", 1)[1] + ".zip") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self._act(lambda: self.store.export_zip(identifier, Path(dialog.GetPath())))

    def activate(self, evt):
        identifier = self._act(self.selected)
        if identifier:
            import config
            from . import SECTION
            config.conf[SECTION][self.setting_key] = identifier
            self.plugin.reload_sounds()


class ThemeEditor(wx.Dialog):
    def __init__(self, parent, plugin, store, identifier):
        name = store.load(identifier)["name"]
        super().__init__(parent, title=_("Edit sound theme: %s") % name, size=(750, 600),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.plugin = plugin
        self.store = store
        self.identifier = identifier
        self._description_timer = None
        catalog = all_keyboard_events() if store.kind == "keyboard" else all_events(Role, State)
        self.entries = [(group, key, label) for group, key, label in catalog
                        if store.accepts(key)]
        self.groups = sorted({group for group, _, _ in self.entries})
        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(wx.StaticText(self, label=_("&Event category:")), 0, wx.ALL, 8)
        self.group = wx.Choice(self, choices=self.groups)
        self.group.SetName(_("Event category"))
        main.Add(self.group, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        main.Add(wx.StaticText(self, label=_("Choose an &event to assign a WAV file:")), 0, wx.ALL, 8)
        self.events = wx.ListBox(self)
        self.events.SetName(_("Sound events"))
        main.Add(self.events, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        main.Add(wx.StaticText(self, label=_("Where and when this sound is used:")),
                 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.event_help = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE,
                                      size=(-1, 64))
        self.event_help.SetName(_("Description of selected sound event"))
        main.Add(self.event_help, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.announce_help = wx.CheckBox(self, label=_(
            "Speak the event description when moving through the list"))
        self.announce_help.SetValue(True)
        main.Add(self.announce_help, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.path_label = wx.StaticText(self, label=_("Sound file: none"))
        main.Add(self.path_label, 0, wx.ALL, 8)
        if store.kind == "keyboard":
            main.Add(wx.StaticText(self, label=_("Press a key in the field below to select and preview its sound:")),
                     0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
            self.capture = wx.TextCtrl(self, style=wx.TE_READONLY)
            self.capture.SetName(_("Capture and preview a physical key"))
            self.capture.SetValue(_("Focus here and press a key, including Tab or F1–F12"))
            main.Add(self.capture, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            self.capture.Bind(wx.EVT_CHAR_HOOK, self.on_key_capture)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        actions = [(_("&Replace WAV..."), self.assign)]
        if store.kind != "keyboard":
            actions.append((_("Add WAV &variation..."), self.append))
        actions.extend([(_("&Preview"), self.preview), (_("&Remove assignment"), self.remove)])
        for title, callback in actions:
            button = wx.Button(self, label=title)
            button.Bind(wx.EVT_BUTTON, callback)
            buttons.Add(button, 0, wx.RIGHT, 6)
        main.Add(buttons, 0, wx.ALL, 8)
        close = wx.Button(self, wx.ID_CLOSE, _("&Done"))
        close.Bind(wx.EVT_BUTTON, self.on_done)
        main.Add(close, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        self.SetSizer(main)
        self.group.Bind(wx.EVT_CHOICE, self.on_group)
        self.events.Bind(wx.EVT_LISTBOX, self.on_select)
        self.group.SetSelection(0)
        self.on_group(None)

    def on_group(self, evt):
        if not self.groups:
            return
        label = self.groups[self.group.GetSelection()]
        self.visible = [(key, name) for group, key, name in self.entries if group == label]
        # Keep the names unprefixed for first-letter keyboard navigation.
        # Assignment details are in the separate Sound file label below.
        self.events.Set([name for key, name in self.visible])
        if self.visible:
            self.events.SetSelection(0)
        self.on_select(evt)

    def selected_key(self):
        index = self.events.GetSelection()
        return self.visible[index][0] if 0 <= index < len(self.visible) else None

    def on_select(self, evt):
        key = self.selected_key()
        label = self.visible[self.events.GetSelection()][1] if key else ""
        explanation = event_description(key, label, languageHandler.getLanguage()) if key else ""
        self.event_help.SetValue(explanation)
        if self._description_timer is not None:
            self._description_timer.Stop()
            self._description_timer = None
        if evt is not None and key and self.announce_help.GetValue():
            # Let NVDA announce the bare list item first; a quick series of
            # arrow presses must never queue stale, wordy descriptions.
            self._description_timer = wx.CallLater(170, self._announce_event, key, explanation)
        mapping = self.store.load(self.identifier)["sounds"]
        value = mapping.get(key)
        description = (_("%d sound variations") % len(value) if isinstance(value, list)
                       else value or _("none (fallback may apply)"))
        self.path_label.SetLabel(_("Sound file: %s") % description)
        if evt is not None and key:
            path = self.store.sound_for(self.identifier, key)
            if path is not None:
                try:
                    self.plugin.audio.preview_file(path, self.plugin.setting("volume"))
                except (ValueError, OSError):
                    pass

    def _announce_event(self, key, explanation):
        self._description_timer = None
        if self.selected_key() == key and self.announce_help.GetValue():
            ui.message(explanation)

    def on_done(self, evt):
        if self._description_timer is not None:
            self._description_timer.Stop()
            self._description_timer = None
        self.EndModal(wx.ID_CLOSE)

    def on_key_capture(self, event):
        """Consume keystrokes only in this field; keep Tab accessible elsewhere."""
        raw = event.GetRawKeyCode()
        code = raw if 1 <= raw <= 255 else event.GetKeyCode()
        if not 1 <= code <= 255:
            event.Skip()
            return
        flags = event.GetRawKeyFlags()
        selected = event_for_virtual_key(code, (flags >> 16) & 0xFF, bool(flags & 0x0100))
        for group, key, _ in self.entries:
            if key != selected:
                continue
            self.group.SetSelection(self.groups.index(group))
            self.on_group(None)
            for row, (candidate, _) in enumerate(self.visible):
                if candidate == key:
                    self.events.SetSelection(row)
                    self.on_select(None)
                    break
            break
        self.capture.SetValue(_("Key: %s") % name_for_event(selected))
        path = self.store.sound_for(self.identifier, selected)
        if path is not None:
            try:
                self.plugin.audio.preview_file(path, self.plugin.setting("volume"))
            except (ValueError, OSError) as error:
                explain_error(self, error)

    def _act(self, callback):
        try:
            callback()
            self.plugin.reload_sounds()
            index = self.events.GetSelection()
            self.on_group(None)
            if index >= 0:
                self.events.SetSelection(index)
                self.on_select(None)
        except (ValueError, OSError, KeyError, PermissionError) as error:
            explain_error(self, error)

    def _pick_wav(self, append: bool):
        key = self.selected_key()
        if not key:
            return
        with wx.FileDialog(self, _("Choose uncompressed WAV"),
                           wildcard="WAV files (*.wav)|*.wav", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                return
            path = Path(dialog.GetPath())
        self._act(lambda: self.store.assign(self.identifier, key, path, append=append))

    def assign(self, evt):
        self._pick_wav(False)

    def append(self, evt):
        self._pick_wav(True)

    def remove(self, evt):
        key = self.selected_key()
        if key:
            self._act(lambda: self.store.assign(self.identifier, key, None))

    def preview(self, evt):
        key = self.selected_key()
        if not key:
            return
        path = self.store.sound_for(self.identifier, key)
        if path is None:
            wx.MessageBox(_("No sound is assigned to this event"), _("Preview"), parent=self)
            return
        try:
            self.plugin.audio.preview_file(path, self.plugin.setting("volume"))
        except (ValueError, OSError) as error:
            explain_error(self, error)
