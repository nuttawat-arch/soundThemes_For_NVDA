"""NVDA-independent, executable smoke tests for the three settings windows.

The sound engine tests cannot catch an exception while wx constructs a dialog.
This intentionally small wx shim checks that our constructors and menu error
boundary still execute. Only live NVDA on Windows can certify native focus.
"""

import ast
import builtins
from contextlib import contextmanager
import importlib
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "globalPlugins" / "soundThemes"


class Widget:
    def __init__(self, *args, **kwargs):
        self.selection = -1
        self.label = kwargs.get("label", args[2] if len(args) > 2 else None)
        self.value = kwargs.get("value", False)
        self.items = list(kwargs.get("choices", ()))
        self.bindings = {}
        self.children = []

    def Bind(self, event, callback, **kwargs):
        self.bindings[event] = callback
        if "id" in kwargs:
            self.bindings[(event, kwargs["id"])] = callback

    def SetName(self, name):
        self.name = name

    def SetFocus(self):
        self.focused = True

    def SetValue(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def SetLabel(self, value):
        self.label = value

    def Set(self, items):
        self.items = list(items)

    def SetSelection(self, selection):
        self.selection = selection

    def GetSelection(self):
        return self.selection

    def SetSizer(self, sizer):
        self.sizer = sizer

    def SetScrollRate(self, *args):
        pass

    def Enable(self, value):
        self.enabled = value

    def Add(self, item, *args, **kwargs):
        self.children.append(item)
        return item

    def AddPage(self, page, label):
        self.children.append((page, label))

    def AddGrowableCol(self, *args):
        pass

    def SetEscapeId(self, identifier):
        self.escape_id = identifier

    def CreateSeparatedButtonSizer(self, flags):
        return Widget()

    def ShowModal(self):
        return 0

    def Destroy(self):
        self.destroyed = True

    def EndModal(self, value):
        self.modal_result = value


class Helper:
    def __init__(self, parent, sizer):
        self.sizer = sizer

    def addItem(self, item):
        self.sizer.Add(item)
        return item


@contextmanager
def fake_nvda_gui():
    """Install only the NVDA/wx modules needed to construct real source UIs."""
    wx = types.ModuleType("wx")
    for name in (
        "Dialog", "ScrolledWindow", "Panel", "StaticText", "Choice", "CheckBox",
        "SpinCtrl", "Slider", "Button", "Notebook", "ListBox", "TextCtrl",
        "BoxSizer", "FlexGridSizer", "TextEntryDialog", "FileDialog",
        "SingleChoiceDialog", "CloseEvent",
    ):
        setattr(wx, name, type(name, (Widget,), {}))
    for name in (
        "TAB_TRAVERSAL", "VSCROLL", "VERTICAL", "HORIZONTAL", "ALL", "EXPAND",
        "LEFT", "RIGHT", "TOP", "BOTTOM", "ALIGN_RIGHT", "RESIZE_BORDER",
        "DEFAULT_DIALOG_STYLE", "OK", "CANCEL", "APPLY", "ID_OK", "ID_CANCEL", "ID_APPLY", "ID_NONE",
        "EVT_BUTTON", "EVT_CHOICE", "EVT_CHECKBOX", "EVT_LISTBOX",
        "EVT_CHAR_HOOK", "EVT_CLOSE", "EVT_SHOW", "TE_READONLY", "TE_MULTILINE", "LB_SINGLE",
        "NOT_FOUND", "WXK_ESCAPE", "WXK_TAB", "WXK_SPACE",
        "YES", "NO", "YES_NO", "NO_DEFAULT", "ICON_WARNING",
    ):
        setattr(wx, name, -1 if name == "NOT_FOUND" else 1)
    # Preserve distinctions that matter for modal outcomes and Escape.
    wx.YES = 10
    wx.NO = 11
    wx.ID_YES = 10
    wx.ID_NO = 11
    wx.ID_CANCEL = 12
    wx.ID_APPLY = 13
    wx.APPLY = 4
    wx.ID_NONE = -3
    wx.WXK_ESCAPE = 27
    wx.WXK_TAB = 9
    wx.WXK_SPACE = 32

    addon = types.ModuleType("addonHandler")
    addon.initTranslation = lambda: None
    language = types.ModuleType("languageHandler")
    language.getLanguage = lambda: "en"
    ui = types.ModuleType("ui")
    ui.message = lambda *args: None
    control_types = types.ModuleType("controlTypes")
    control_types.Role = ()
    control_types.State = ()
    gui = types.ModuleType("gui")
    gui.guiHelper = types.SimpleNamespace(BoxSizerHelper=Helper)
    package = types.ModuleType("sound_themes_settings_smoke")
    package.__path__ = [str(PACKAGE_ROOT)]
    replacements = {
        "wx": wx,
        "addonHandler": addon,
        "languageHandler": language,
        "ui": ui,
        "controlTypes": control_types,
        "gui": gui,
        package.__name__: package,
    }
    original = {name: sys.modules.get(name) for name in replacements}
    existing_translation = getattr(builtins, "_", None)
    builtins._ = lambda text: text
    sys.modules.update(replacements)
    try:
        yield importlib.import_module("sound_themes_settings_smoke.settings"), wx
    finally:
        for name in list(sys.modules):
            if name.startswith("sound_themes_settings_smoke."):
                del sys.modules[name]
        for name, previous in original.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
        if existing_translation is None:
            del builtins._
        else:
            builtins._ = existing_translation


class Store:
    def __init__(self, kind):
        self.kind = kind
        self.embedded = True

    def themes(self):
        return [("user:sample", "Sample")]

    def playback_mode(self, identifier):
        return "combined"

    def directory(self, identifier):
        return ROOT / "globalPlugins/soundThemes/effects" / self.kind / "sample"

    def load(self, identifier):
        return {"name": "Sample", "sounds": {}}

    def accepts(self, key):
        return True


class Plugin:
    def __init__(self):
        self.navigation_store = Store("navigation")
        self.typing_store = Store("typing")
        self.keyboard_store = Store("keyboard")
        self._updater = types.SimpleNamespace(check=lambda manual: None)

    def setting(self, name):
        return {"theme": "user:sample", "typingTheme": "user:sample",
                "keyboardTheme": "user:sample", "hoverDelay": 270,
                "volume": 65}.get(name, False)

    def reload_sounds(self):
        pass


class SettingsSmokeTests(unittest.TestCase):
    def test_apply_saves_and_reloads_without_closing_settings(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            reloaded = []
            checks_reconfigured = []
            plugin.reload_sounds = lambda: reloaded.append(True)
            plugin._updater.configure_auto_checks = lambda: checks_reconfigured.append(True)
            config = types.ModuleType("config")
            config.conf = {"soundThemes": {
                "volume": 65, "enabled": True, "updateCheckIntervalMinutes": 180,
            }}
            sys.modules[settings.__package__].SECTION = "soundThemes"
            with mock.patch.dict(sys.modules, {"config": config}):
                dialog = settings.SoundSettingsDialog(None, plugin)
                dialog.panel.volume.SetValue(71)
                dialog.panel.checkForUpdates.SetValue(True)
                self.assertTrue(dialog.on_apply(None))
                self.assertFalse(hasattr(dialog, "modal_result"))
                self.assertEqual(config.conf["soundThemes"]["volume"], 71)
                self.assertTrue(config.conf["soundThemes"]["checkForUpdates"])
                self.assertEqual(config.conf["soundThemes"]["updateCheckIntervalMinutes"], 180)
                self.assertEqual(len(reloaded), 1)
                self.assertEqual(len(checks_reconfigured), 1)

                # Edits made after Apply remain unapplied when Cancel closes.
                dialog.panel.volume.SetValue(99)
                dialog.EndModal(wx.ID_CANCEL)
                self.assertEqual(config.conf["soundThemes"]["volume"], 71)

                next_dialog = settings.SoundSettingsDialog(None, plugin)
                next_dialog.panel.volume.SetValue(76)
                next_dialog.on_save(None)
                self.assertEqual(next_dialog.modal_result, wx.ID_OK)
                self.assertEqual(config.conf["soundThemes"]["volume"], 76)
                self.assertEqual(len(reloaded), 2)

    def test_failed_apply_does_not_close_settings(self):
        with fake_nvda_gui() as (settings, wx):
            dialog = settings.SoundSettingsDialog(None, Plugin())
            errors = []
            settings.explain_error = lambda parent, error: errors.append(str(error))
            dialog.panel.onSave = lambda: (_ for _ in ()).throw(ValueError("invalid sound"))
            self.assertFalse(dialog.on_apply(None))
            dialog.on_save(None)
            self.assertFalse(hasattr(dialog, "modal_result"))
            self.assertEqual(errors, ["invalid sound", "invalid sound"])

    def test_settings_dialog_focuses_navigation_theme_after_it_opens(self):
        with fake_nvda_gui() as (settings, wx):
            scheduled = []
            wx.CallAfter = lambda callback: scheduled.append(callback)
            dialog = settings.SoundSettingsDialog(None, Plugin())
            self.assertEqual(dialog.panel.theme.name, "Navigation sound theme")
            self.assertFalse(getattr(dialog.panel.theme, "focused", False))

            skipped = []
            show_event = lambda shown: types.SimpleNamespace(
                IsShown=lambda: shown, Skip=lambda: skipped.append(True))
            dialog.bindings[wx.EVT_SHOW](show_event(False))
            self.assertEqual(scheduled, [], "Hiding must not steal focus")
            dialog.bindings[wx.EVT_SHOW](show_event(True))
            self.assertEqual(len(scheduled), 1)
            self.assertFalse(getattr(dialog.panel.theme, "focused", False))
            scheduled.pop()()
            self.assertTrue(dialog.panel.theme.focused)
            self.assertEqual(skipped, [True, True])

    def test_space_replays_selected_theme_or_sound_without_leaving_list(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            played = []
            plugin.audio = types.SimpleNamespace(
                preview_file=lambda path, volume: played.append((str(path), volume)))
            plugin.navigation_store.sound_for = lambda theme_id, key: ROOT / "sample.wav"
            original_preview = settings.preview_selected_theme
            settings.preview_selected_theme = lambda plugin, store, identifier: played.append(identifier)
            try:
                manager = settings.ThemeManagerPage(None, plugin, plugin.navigation_store, "navigation")
                editor = settings.ThemeEditor(None, plugin, plugin.navigation_store, "user:sample")
                self.assertIn("Space", manager.theme_list.name)
                self.assertIn("Space", editor.events.name)

                skipped = []
                def key_event(code, ctrl=False):
                    return types.SimpleNamespace(
                        GetKeyCode=lambda: code, ControlDown=lambda: ctrl,
                        AltDown=lambda: False, ShiftDown=lambda: False,
                        Skip=lambda: skipped.append(True),
                    )

                manager.theme_list.bindings[wx.EVT_CHAR_HOOK](key_event(wx.WXK_SPACE))
                self.assertIn("user:sample", played)
                self.assertEqual(manager.theme_list.GetSelection(), 0)
                editor.events.bindings[wx.EVT_CHAR_HOOK](key_event(wx.WXK_SPACE))
                self.assertIn((str(ROOT / "sample.wav"), 65), played)
                self.assertEqual(editor.events.GetSelection(), 0)

                before = len(played)
                manager.on_theme_key(key_event(wx.WXK_SPACE, ctrl=True))
                editor.on_event_key(key_event(wx.WXK_TAB))
                self.assertEqual(len(played), before)
                self.assertEqual(skipped, [True, True])
            finally:
                settings.preview_selected_theme = original_preview

    def test_update_changelog_dialog_and_repeating_schedule_without_nvda(self):
        with fake_nvda_gui() as (settings, wx):
            module = ast.parse((PACKAGE_ROOT / "updater.py").read_text(encoding="utf-8"))
            declarations = [node for node in module.body
                            if isinstance(node, ast.ClassDef) and
                            node.name in ("ReleaseNotesDialog", "UpdateChecker")]
            config = types.SimpleNamespace(conf={"soundThemes": {
                "checkForUpdates": True, "updateCheckIntervalMinutes": 180,
            }})
            timers = []

            class Timer:
                def __init__(self, ms, callback):
                    self.ms, self.callback, self.stopped = ms, callback, False

                def Stop(self):
                    self.stopped = True

            wx.CallLater = lambda ms, callback: timers.append(Timer(ms, callback)) or timers[-1]
            scope = {"wx": wx, "_": lambda value: value, "threading": threading,
                     "config": config, "SECTION": "soundThemes", "STARTUP_DELAY_MS": 15000,
                     "AUTO_CHECK_INTERVAL_MS": 30 * 60000,
                     "_managed_by_store": lambda: False,
                     "globalVars": types.SimpleNamespace(appArgs=types.SimpleNamespace(secure=False))}
            exec(compile(ast.Module(body=declarations, type_ignores=[]),
                         "<updater-smoke>", "exec"), scope)
            release = types.SimpleNamespace(version="0.17.4", notes="New audio controls\nFaster checks")
            dialog = scope["ReleaseNotesDialog"](None, "0.17.3", release)
            self.assertEqual(dialog.notes.value, release.notes)
            self.assertEqual(dialog.escape_id, wx.ID_NO)
            dialog.on_close(None)
            self.assertEqual(dialog.modal_result, wx.ID_NO)

            updater = scope["UpdateChecker"]()
            updater.configure_auto_checks()
            self.assertEqual(timers[-1].ms, 15000)
            checks = []
            updater.check = lambda manual=False: checks.append(manual)
            updater._periodic_tick()
            self.assertEqual(checks, [False])
            self.assertEqual(timers[-1].ms, 30 * 60000)
            config.conf["soundThemes"]["updateCheckIntervalMinutes"] = 10
            updater._periodic_tick()
            self.assertEqual(timers[-1].ms, 30 * 60000)
            config.conf["soundThemes"]["checkForUpdates"] = False
            updater.configure_auto_checks()
            self.assertTrue(timers[-1].stopped)
            updater.terminate()

    def test_settings_ui_has_no_diagnostic_report_and_creation_has_short_label(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            dialog = settings.SoundSettingsDialog(None, plugin)
            settings_labels = [item.label for item in dialog.panel.sizer.children
                               if isinstance(item, wx.Button)]
            self.assertNotIn("&Sound playback report...", settings_labels)
            self.assertFalse(any("report" in label.lower() for label in settings_labels))
            self.assertFalse(hasattr(dialog.panel, "on_audio_report"))

            update_options = [item.label for item in dialog.panel.sizer.children
                              if isinstance(item, (wx.Button, wx.CheckBox))
                              and "update" in (item.label or "").lower()]
            self.assertIn("&Automatically check for updates", update_options)
            self.assertIn("Check for &updates now", update_options)
            self.assertFalse(hasattr(dialog.panel, "updateInterval"))
            self.assertFalse(any("frequency" in str(getattr(item, "label", "")).lower()
                                 for item in dialog.panel.sizer.children))

            self.assertIn((wx.EVT_BUTTON, wx.ID_APPLY), dialog.bindings)
            self.assertIn((wx.EVT_BUTTON, wx.ID_OK), dialog.bindings)

            for store in (plugin.navigation_store, plugin.typing_store,
                          plugin.keyboard_store):
                with self.subTest(kind=store.kind):
                    page = settings.ThemeManagerPage(None, plugin, store, store.kind)
                    button_grid = next(item for item in page.sizer.children
                                       if isinstance(item, wx.FlexGridSizer))
                    buttons = [item.label for item in button_grid.children
                               if isinstance(item, wx.Button)]
                    self.assertIn("&Create", buttons)
                    self.assertNotIn("&Create or copy a theme...", buttons)

    def test_settings_window_and_manager_build_without_runtime_exceptions(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            dialog = settings.SoundSettingsDialog(None, plugin)
            self.assertEqual(dialog.escape_id, wx.ID_CANCEL)
            self.assertEqual(dialog.panel.theme.items, ["Sample"])
            self.assertEqual(dialog.panel.typing_theme.items, ["Sample"])
            self.assertEqual(dialog.panel.keyboard_theme.items, ["Sample"])
            manager = settings.ThemeManager(dialog, plugin)
            self.assertEqual(manager.escape_id, wx.ID_CANCEL)

    def test_sound_editors_build_for_every_sound_category(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            for store in (plugin.navigation_store, plugin.typing_store,
                          plugin.keyboard_store):
                with self.subTest(kind=store.kind):
                    editor = settings.ThemeEditor(None, plugin, store, "user:sample")
                    self.assertEqual(editor.escape_id, wx.ID_NONE)
                    self.assertTrue(editor.visible)

    def test_escape_preserves_changed_wavs_until_yes_confirms_discard(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            editor = settings.ThemeEditor(None, plugin, plugin.navigation_store, "user:sample")
            editor.session.has_changes = lambda: True
            rolled_back = []
            editor.session.rollback = lambda: rolled_back.append(True)
            wx.MessageBox = lambda *args: wx.NO
            evt = types.SimpleNamespace(GetKeyCode=lambda: wx.WXK_ESCAPE)
            editor.on_escape(evt)
            self.assertEqual(rolled_back, [])
            self.assertFalse(hasattr(editor, "modal_result"))
            wx.MessageBox = lambda *args: wx.YES
            editor.on_escape(evt)
            self.assertEqual(rolled_back, [True])
            self.assertEqual(editor.modal_result, wx.ID_CANCEL)

    def test_tools_callback_opens_and_destroys_window_on_success(self):
        tree = ast.parse((PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == "GlobalPlugin")
        show = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_show_settings")
        steps = []
        class Dialog:
            def __init__(self, parent, plugin):
                steps.append("constructed")
            def ShowModal(self):
                steps.append("opened")
            def Destroy(self):
                steps.append("destroyed")
        fake_settings = types.ModuleType("sound_themes_menu_success.settings")
        fake_settings.SoundSettingsDialog = Dialog
        fake_package = types.ModuleType("sound_themes_menu_success")
        fake_package.__path__ = []
        old_package = sys.modules.get(fake_package.__name__)
        sys.modules[fake_package.__name__] = fake_package
        sys.modules[fake_settings.__name__] = fake_settings
        try:
            frame = types.SimpleNamespace(prePopup=lambda: steps.append("prePopup"),
                                          postPopup=lambda: steps.append("postPopup"))
            scope = {"__package__": fake_package.__name__,
                     "gui": types.SimpleNamespace(mainFrame=frame),
                     "log": types.SimpleNamespace(error=lambda *a, **k: steps.append("error")),
                     "wx": types.SimpleNamespace(OK=1, ICON_ERROR=2),
                     "_": lambda value: value}
            exec(compile(ast.Module(body=[show], type_ignores=[]), "<tools-menu>", "exec"), scope)
            plugin = types.SimpleNamespace(_closed=False, _settings_open=False)
            scope["_show_settings"](plugin)
            self.assertEqual(steps, ["prePopup", "constructed", "opened", "destroyed", "postPopup"])
            self.assertFalse(plugin._settings_open)
        finally:
            sys.modules.pop(fake_settings.__name__, None)
            if old_package is None:
                sys.modules.pop(fake_package.__name__, None)
            else:
                sys.modules[fake_package.__name__] = old_package

    def test_tools_callback_reports_window_failure_and_resets_busy_state(self):
        tree = ast.parse((PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8"))
        plugin_class = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                            and node.name == "GlobalPlugin")
        show = next(node for node in plugin_class.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_show_settings")
        captured = []
        parent = types.SimpleNamespace(prePopup=lambda: None, postPopup=lambda: None)
        fake_gui = types.SimpleNamespace(mainFrame=parent)
        wx = types.SimpleNamespace(OK=1, ICON_ERROR=2, MessageBox=lambda *args: captured.append("message"))
        fake_log = types.SimpleNamespace(error=lambda *args, **kwargs: captured.append("logged"))
        fake_settings = types.ModuleType("sound_themes_menu_smoke.settings")
        def fail(*args):
            raise RuntimeError("test window construction error")
        fake_settings.SoundSettingsDialog = fail
        fake_package = types.ModuleType("sound_themes_menu_smoke")
        fake_package.__path__ = []
        originals = {name: sys.modules.get(name) for name in
                     (fake_package.__name__, fake_settings.__name__)}
        sys.modules[fake_package.__name__] = fake_package
        sys.modules[fake_settings.__name__] = fake_settings
        try:
            globals_ = {"__package__": fake_package.__name__, "gui": fake_gui,
                        "wx": wx, "log": fake_log, "_": lambda value: value,
                        "ui": types.SimpleNamespace(message=lambda *args: captured.append("spoken"))}
            exec(compile(ast.Module(body=[show], type_ignores=[]), "<tools-menu>", "exec"), globals_)
            plugin = types.SimpleNamespace(_closed=False, _settings_open=False)
            globals_["_show_settings"](plugin)
            self.assertFalse(plugin._settings_open)
            self.assertIn("logged", captured)
            self.assertIn("message", captured)
        finally:
            for name, previous in originals.items():
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous
