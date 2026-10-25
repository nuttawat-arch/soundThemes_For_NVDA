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
import types
import unittest


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

    def SetName(self, name):
        self.name = name

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
        "DEFAULT_DIALOG_STYLE", "OK", "CANCEL", "ID_OK", "ID_CANCEL", "ID_NONE",
        "EVT_BUTTON", "EVT_CHOICE", "EVT_CHECKBOX", "EVT_LISTBOX",
        "EVT_CHAR_HOOK", "EVT_CLOSE", "TE_READONLY", "TE_MULTILINE", "LB_SINGLE",
        "NOT_FOUND", "WXK_ESCAPE", "WXK_TAB",
        "YES", "NO", "YES_NO", "NO_DEFAULT", "ICON_WARNING",
    ):
        setattr(wx, name, -1 if name == "NOT_FOUND" else 1)
    # Preserve distinctions that matter for modal outcomes and Escape.
    wx.YES = 10
    wx.NO = 11
    wx.ID_CANCEL = 12
    wx.ID_NONE = -3
    wx.WXK_ESCAPE = 27
    wx.WXK_TAB = 9

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
    def test_settings_ui_has_no_diagnostic_report_and_creation_has_short_label(self):
        with fake_nvda_gui() as (settings, wx):
            plugin = Plugin()
            dialog = settings.SoundSettingsDialog(None, plugin)
            settings_labels = [item.label for item in dialog.panel.sizer.children
                               if isinstance(item, wx.Button)]
            self.assertNotIn("&Sound playback report...", settings_labels)
            self.assertFalse(any("report" in label.lower() for label in settings_labels))
            self.assertFalse(hasattr(dialog.panel, "on_audio_report"))

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
