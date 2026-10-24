"""Regression suite for NVDA-independent sound packs and keyboard context."""

from __future__ import annotations

import importlib
import importlib.util
import ast
import io
import json
import queue
import struct
import sys
import tempfile
import threading
import time
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "globalPlugins" / "soundThemes"
package = types.ModuleType("nvda_sound_testpackage")
package.__path__ = [str(PACKAGE_ROOT)]
sys.modules[package.__name__] = package
catalog = importlib.import_module("nvda_sound_testpackage.catalog")
packs = importlib.import_module("nvda_sound_testpackage.folderpacks")
audio = importlib.import_module("nvda_sound_testpackage.audio")
browse_events = importlib.import_module("nvda_sound_testpackage.browse_events")
browse_module = importlib.import_module("nvda_sound_testpackage.browser")
keys_module = importlib.import_module("nvda_sound_testpackage.keyboard_state")
keyboard_catalog = importlib.import_module("nvda_sound_testpackage.keyboard_catalog")
modes = importlib.import_module("nvda_sound_testpackage.modes")
focus_policy = importlib.import_module("nvda_sound_testpackage.focus_policy")
merge_spec = importlib.util.spec_from_file_location(
    "soundthemes_original_audio_merge", ROOT / "scripts" / "import_original_audio.py")
original_audio = importlib.util.module_from_spec(merge_spec)
merge_spec.loader.exec_module(original_audio)
kliq_spec = importlib.util.spec_from_file_location(
    "soundthemes_kliq_audio_merge", ROOT / "scripts" / "import_kliq_audio.py")
kliq_audio = importlib.util.module_from_spec(kliq_spec)
kliq_spec.loader.exec_module(kliq_audio)
effects_spec = importlib.util.spec_from_file_location(
    "soundthemes_effects_merge", ROOT / "scripts" / "import_effects_archive.py")
effects_merge = importlib.util.module_from_spec(effects_spec)
effects_spec.loader.exec_module(effects_merge)


def make_wav(path, bits=16):
    samples = [-8000, 9000, -4000, 7000]
    if bits == 8:
        raw = bytes((0, 127, 255, 128))
    elif bits == 16:
        raw = struct.pack("<4h", *samples)
    elif bits == 24:
        raw = b"".join(n.to_bytes(3, "little", signed=True) for n in samples)
    elif bits == 32:
        raw = struct.pack("<4i", *samples)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(bits // 8)
        wav.setframerate(22050)
        wav.writeframes(raw)


class SoundThemeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.sample = self.home / "test.wav"
        make_wav(self.sample)
        self.nav = packs.ThemeStore(self.home / "built-nav", self.home / "soundThemes/effects/navigation", "navigation")
        self.typing = packs.ThemeStore(self.home / "built-type", self.home / "soundThemes/effects/typing", "typing")
        self.keyboard = packs.ThemeStore(self.home / "built-keys", self.home / "soundThemes/effects/keyboard", "keyboard")
        builtin = self.nav.packaged / "balanced"
        builtin.mkdir(parents=True)
        (builtin / "role.default.wav").write_bytes(self.sample.read_bytes())
        (builtin / "system.lock.wav").write_bytes(self.sample.read_bytes())

    def test_builtin_copy_and_mutate_only_user_folder(self):
        with self.assertRaises(PermissionError):
            self.nav.assign("builtin:balanced", "role.button", self.sample)
        theme = self.nav.create("My Personal Sound", "builtin:balanced")
        self.assertEqual(theme, "user:my-personal-sound")
        self.assertFalse((self.nav.directory(theme) / "theme.json").exists())
        self.nav.assign(theme, "role.button", self.sample)
        self.assertTrue(self.nav.sound_for(theme, "role.button").exists())
        self.assertNotIn("role.button", self.nav.load("builtin:balanced")["sounds"])
        self.nav.assign(theme, "role.button", None)
        self.assertFalse("role.button" in self.nav.load(theme)["sounds"])
        self.assertTrue(any((self.nav.directory(theme) / "_unused").iterdir()))
        renamed = self.nav.rename(theme, "New name")
        self.assertEqual(renamed, "user:new-name")
        self.assertFalse(self.nav.directory(theme).exists())
        self.nav.delete(renamed)
        self.assertFalse(self.nav.directory(renamed).exists())

    def test_any_builtin_preset_can_be_deleted_and_restored_without_erasing_installer_audio(self):
        builtin = self.nav.packaged / "balanced"
        self.assertIn("builtin:balanced", dict(self.nav.themes()))
        self.nav.delete("builtin:balanced")
        self.assertTrue((builtin / "role.default.wav").exists())
        self.assertNotIn("builtin:balanced", dict(self.nav.themes()))
        with self.assertRaises(FileNotFoundError):
            self.nav.load("builtin:balanced")
        self.assertEqual(self.nav.removed_builtins(), [("builtin:balanced", "Balanced")])
        # User preference must survive restarting the plugin and any update
        # replacing the read-only installed sound pack.
        restarted = packs.ThemeStore(self.nav.packaged, self.nav.writable, "navigation")
        self.assertEqual(restarted.themes(), [])
        restarted.restore_builtin("builtin:balanced")
        self.assertIn("builtin:balanced", dict(restarted.themes()))
        self.assertEqual(restarted.removed_builtins(), [])
        restarted.delete("builtin:balanced")
        self.assertEqual(restarted.themes(), [])  # never create a forced default

    def test_deleted_preset_is_scoped_to_its_category_and_custom_names_remain_usable(self):
        (self.typing.packaged / "balanced").mkdir(parents=True)
        make_wav(self.typing.packaged / "balanced" / "key.character.wav")
        self.nav.delete("builtin:balanced")
        self.assertIn("builtin:balanced", dict(self.typing.themes()))
        self.assertTrue(self.nav.create("Balanced").startswith("user:"))
        self.assertIn("user:balanced", dict(self.nav.themes()))

    def test_typing_key_fallback_prefers_exact_recording_in_same_pack(self):
        for event in ("key.enter", "key.space", "key.backspace", "key.protected"):
            self.assertEqual(catalog.candidates(event), (event, "key.character"))
        theme = self.typing.create("Sparse Typing")
        self.typing.assign(theme, "key.character", self.sample)
        for event in ("key.enter", "key.space", "key.backspace"):
            self.assertEqual(self.typing.sound_for(theme, event).name, "key.character.wav")
        dedicated = self.home / "dedicated.wav"
        make_wav(dedicated)
        self.typing.assign(theme, "key.enter", dedicated)
        self.assertEqual(self.typing.sound_for(theme, "key.enter").name, "key.enter.wav")
        self.assertEqual(self.typing.sound_for(theme, "key.space").name, "key.character.wav")
        self.assertIsNone(self.nav.sound_for("builtin:balanced", "key.enter"))

    def test_raw_special_typing_is_not_doubled_by_later_nvda_typed_character(self):
        keys = keys_module.KeyboardState()
        keys.note_typing_special("key.space")
        self.assertFalse(keys.consume_typing_special("key.enter"))
        self.assertTrue(keys.consume_typing_special("key.space"))
        self.assertFalse(keys.consume_typing_special("key.space"))
        keys.note_typing_special("key.backspace")
        keys.clear()
        self.assertFalse(keys.consume_typing_special("key.backspace"))
        plugin = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("self._focused_editable()", plugin)
        self.assertIn("self.keys.note_typing_special(special)", plugin)
        self.assertIn("self.keys.consume_typing_special(event)", plugin)
        self.assertNotIn("self._ensure_keyboard_theme()", plugin)
        ui_source = (PACKAGE_ROOT / "settings.py").read_text(encoding="utf-8")
        self.assertNotIn("Import old sounds &folder", ui_source)
        self.assertIn("Restore removed presets", ui_source)

    def test_browse_role_cues_resolve_virtual_cursor_objects_and_quick_nav_hints(self):
        root = types.SimpleNamespace(role="DOCUMENT")
        button = types.SimpleNamespace(role="BUTTON")
        link = types.SimpleNamespace(role="LINK")
        heading = types.SimpleNamespace(role="HEADING")

        def info(obj, focusable=None):
            return types.SimpleNamespace(NVDAObjectAtStart=obj,
                                         focusableNVDAObjectAtStart=focusable)

        self.assertEqual(browse_events.browse_cue(info(button), root=root), "role.button")
        self.assertEqual(browse_events.browse_cue(info(link), root=root), "role.link")
        self.assertEqual(browse_events.browse_cue(info(heading), root=root), "role.heading")
        self.assertEqual(browse_events.browse_cue(info(root, button), root=root), "role.button")
        self.assertEqual(browse_events.browse_cue(
            info(types.SimpleNamespace(role="STATICTEXT"), link), root=root), "role.link")
        self.assertEqual(browse_events.browse_cue(info(root), root=root), "nav.caret")
        self.assertEqual(browse_events.browse_cue(info(root), hint="button", root=root), "role.button")
        self.assertEqual(browse_events.browse_cue(info(root), hint="heading3", root=root), "role.heading")
        self.assertEqual(browse_events.browse_cue(info(root), hint="visitedLink", root=root), "role.link")
        self.assertEqual(browse_events.browse_cue(info(root), hint="menuItem", root=root), "role.menuitem")
        self.assertEqual(browse_events.browse_cue(info(root), hint="toggleButton", root=root), "role.togglebutton")
        self.assertEqual(browse_events.browse_cue(info(root), hint="clickable", root=root), "state.clickable")
        self.assertEqual(browse_events.browse_cue(info(root), hint="error", root=root), "state.invalidentry")
        self.assertEqual(browse_events.browse_cue(info(root), hint="formField", root=root), "nav.caret")

    def test_browser_button_link_and_heading_recordings_exist_in_both_original_packs(self):
        for theme in ("default", "voiceover"):
            folder = ROOT / "globalPlugins" / "soundThemes" / "effects" / "navigation" / theme
            for role in ("button", "link", "heading", "checkbox", "radiobutton", "menuitem"):
                self.assertTrue((folder / f"role.{role}.wav").is_file(), (theme, role))

    def test_browse_monitor_plays_actual_control_once_per_movement_and_restores_hooks(self):
        root = types.SimpleNamespace(role="DOCUMENT")
        button = types.SimpleNamespace(role="BUTTON")
        link = types.SimpleNamespace(role="LINK")
        heading = types.SimpleNamespace(role="HEADING")

        class FakeInfo:
            def __init__(self, position, obj):
                self.position = position
                self.NVDAObjectAtStart = obj
                self.focusableNVDAObjectAtStart = obj

            def copy(self):
                return FakeInfo(self.position, self.NVDAObjectAtStart)

            def compareEndPoints(self, other, mode):
                return self.position - other.position

        class FakeCursor:
            def __init__(self):
                self.position = 0
                self.objects = [root, button, link, heading]

            def makeTextInfo(self, position):
                return FakeInfo(self.position, self.objects[self.position])

            def _caretMovementScriptHelper(self, gesture, unit):
                if self.position < len(self.objects) - 1:
                    self.position += 1
                return "caret-result"

        class FakeBrowse(FakeCursor):
            rootNVDAObject = root

            def _quickNavScript(self, gesture, itemType, direction, errorMessage, readUnit):
                if self.position < len(self.objects) - 1:
                    self.position += 1
                return "quick-result"

        original_quick = FakeBrowse._quickNavScript
        original_caret = FakeCursor._caretMovementScriptHelper
        events = []
        plugin = types.SimpleNamespace(
            browse_moved=lambda info, hint=None, root=None: events.append(
                browse_events.browse_cue(info, hint=hint, root=root)),
            play_event=lambda event: events.append(event),
            setting=lambda key: True,
        )
        with patch.dict(sys.modules, {
                "browseMode": types.SimpleNamespace(BrowseModeTreeInterceptor=FakeBrowse),
                "cursorManager": types.SimpleNamespace(CursorManager=FakeCursor),
                "textInfos": types.SimpleNamespace(POSITION_CARET="caret"),
        }):
            monitor = browse_module.BrowseMonitor(plugin)
            monitor.patch()
            try:
                browse = FakeBrowse()
                self.assertEqual(browse._quickNavScript(None, "button", "next", "", None), "quick-result")
                self.assertEqual(browse._caretMovementScriptHelper(None, "character"), "caret-result")
                self.assertEqual(browse._caretMovementScriptHelper(None, "character"), "caret-result")
                self.assertEqual(events, ["role.button", "role.link", "role.heading"])
                # Movement reaching the end must not create a fake click.
                browse._caretMovementScriptHelper(None, "character")
                self.assertEqual(len(events), 3)
                plain = FakeCursor()
                plain._caretMovementScriptHelper(None, "character")
                self.assertEqual(events[-1], "nav.caret")
                # A failing sound backend must never swallow the NVDA command.
                def failed_audio(*args, **kwargs):
                    raise RuntimeError("audio unavailable")
                plugin.browse_moved = failed_audio
                browse.position = 0
                self.assertEqual(browse._quickNavScript(None, "button", "next", "", None), "quick-result")
                self.assertEqual(browse.position, 1)
            finally:
                monitor.terminate()
        self.assertIs(FakeBrowse._quickNavScript, original_quick)
        self.assertIs(FakeCursor._caretMovementScriptHelper, original_caret)

    def test_import_export_wav_only(self):
        origin = self.nav.create("For Export", "builtin:balanced")
        zip_path = self.home / "export.zip"
        self.nav.export_zip(origin, zip_path)
        with ZipFile(zip_path) as archive:
            self.assertEqual(set(archive.namelist()), {"role.default.wav", "system.lock.wav"})
            self.assertNotIn("theme.json", archive.namelist())
        imported = self.nav.import_zip(zip_path, "Imported Folder")
        self.assertTrue(self.nav.sound_for(imported, "system.lock").exists())

    def test_variations_round_trip_stay_in_same_typing_theme(self):
        theme = self.typing.create("Typing A")
        self.typing.assign(theme, "key.character", self.sample)
        self.typing.assign(theme, "key.character", self.sample, append=True)
        self.assertEqual(len(self.typing.load(theme)["sounds"]["key.character"]), 2)
        zip_path = self.home / "type.zip"
        self.typing.export_zip(theme, zip_path)
        imported = self.typing.import_zip(zip_path, "Typing Import")
        self.assertEqual(len(self.typing.load(imported)["sounds"]["key.character"]), 2)

    def test_accept_all_windows_safe_names(self):
        self.assertEqual(packs.safe_slug("ธีมของนัท"), "ธีมของนัท")
        for name in ("..", "CON", "C:/outside", "../test", "aux", "bad*name"):
            with self.assertRaises(ValueError):
                packs.safe_slug(name)
        for name in ("../escape.wav", "/root.wav", "C:escape.wav", "C:/out.wav"):
            self.assertFalse(self.nav._safe_zip_name(name))

    def test_reject_traversal_zip_without_creating_user_folder(self):
        destination = self.home / "malicious.zip"
        with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
            archive.writestr("../bad.wav", b"invalid")
        with self.assertRaises(ValueError):
            self.nav.import_zip(destination, "Unsafe")
        self.assertFalse(self.nav.directory("user:unsafe").exists())

    def test_unknown_typing_wavs_make_random_pool(self):
        theme = self.typing.create("Typing Custom")
        folder = self.typing.directory(theme)
        for name in ("click-1.wav", "click-2.wav", "typekeyspace.wav", "role.button.wav"):
            (folder / name).write_bytes(self.sample.read_bytes())
        mapping = self.typing.load(theme)["sounds"]
        self.assertEqual(len(mapping["key.character"]), 2)
        self.assertIn("key.space", mapping)
        self.assertNotIn("role.button", mapping)

    def test_reject_parent_with_several_typing_packs(self):
        root = self.home / "legacy"
        for name in ("Set One", "Set Two"):
            folder = root / name
            folder.mkdir(parents=True)
            (folder / "random.wav").write_bytes(self.sample.read_bytes())
        with self.assertRaises(ValueError):
            self.typing.import_legacy_folder(root, "Merged By Mistake")
        imported = self.typing.import_legacy_folder(root / "Set One", "Only One")
        self.assertIn("key.character", self.typing.load(imported)["sounds"])

    def test_import_legacy_keyboard_and_navigation_names_separately(self):
        source = self.home / "old"
        source.mkdir()
        filenames = ("lock.wav", "lockscreen.wav", "unlockscreen.wav", "button.wav",
                     "expanded.wav", "typekeypr.wav", "typekeyspace.wav", "typekey.wav")
        for filename in filenames:
            (source / filename).write_bytes(self.sample.read_bytes())
        nav = self.nav.import_legacy_folder(source, "Original Navigation", roles=["button"])
        keyboard = self.typing.import_legacy_folder(source, "Original Typing", roles=["button"])
        nmap = self.nav.load(nav)["sounds"]
        tmap = self.typing.load(keyboard)["sounds"]
        for event in ("system.lock", "system.lockscreen", "system.unlock", "role.button", "nav.expand"):
            self.assertIn(event, nmap)
        for event in ("key.protected", "key.space", "key.character"):
            self.assertIn(event, tmap)
        self.assertFalse(set(nmap) & set(tmap))

    def test_tab_role_and_tab_keystroke_are_not_conflated(self):
        self.assertEqual(packs.event_for_filename("tab", "navigation", ["tab"]), "role.tab")
        self.assertEqual(packs.event_for_filename("Tab", "navigation", ["tab"]), "key.tab")
        self.assertEqual(packs.event_for_filename("key.tab", "navigation"), "key.tab")
        self.assertEqual(packs.event_for_filename("tab", "typing"), None)

    def test_audio_merger_screenreader_priority_and_all_three_theme_roots(self):
        nav_zip = self.home / "nav.zip"
        destination = self.home / "merged"
        with ZipFile(nav_zip, "w") as archive:
            archive.writestr("button.wav", self.sample.read_bytes())
            archive.writestr("tab.wav", self.sample.read_bytes())
        original_audio.add_navsounds_navigation(nav_zip, destination)
        srs_zip = self.home / "srs.nvda-addon"
        special = self.home / "other.wav"
        make_wav(special, bits=8)
        with ZipFile(srs_zip, "w") as archive:
            archive.writestr("globalPlugins/voiceover/objdata/button.wav", special.read_bytes())
            archive.writestr("globalPlugins/voiceover/Tab.wav", self.sample.read_bytes())
            archive.writestr("globalPlugins/voiceover/typekey.wav", self.sample.read_bytes())
            archive.writestr("globalPlugins/voiceover/delete.wav", self.sample.read_bytes())
            archive.writestr("globalPlugins/voiceover/typekeyremove.wav", special.read_bytes())
            archive.writestr("globalPlugins/voiceover/talkback/one/objdata/button.wav", self.sample.read_bytes())
            archive.writestr("globalPlugins/voiceover/talkback/two/objdata/tab.wav", self.sample.read_bytes())
        report = original_audio.add_screenreader_sounds(srs_zip, destination)
        self.assertEqual(report["distinct_events"], 6)
        self.assertEqual((destination / "navigation/voiceover/role.button.wav").read_bytes(), special.read_bytes())
        self.assertEqual((destination / "navigation/voiceover/role.tab.wav").read_bytes(), self.sample.read_bytes())
        self.assertTrue((destination / "navigation/voiceover/key.tab.wav").is_file())
        self.assertTrue((destination / "navigation/talkback-5/role.button.wav").is_file())
        self.assertTrue((destination / "navigation/talkback-6/role.tab.wav").is_file())
        self.assertTrue((destination / "typing/voiceover/key.character.wav").is_file())
        self.assertEqual((destination / "typing/voiceover/key.backspace.wav").read_bytes(), special.read_bytes())

    def test_audio_merger_rejects_code_only_screenreader(self):
        src = self.home / "no-audio.nvda-addon"
        with ZipFile(src, "w") as archive:
            archive.writestr("globalPlugins/voiceover/__init__.py", "print('never executed')")
        with self.assertRaisesRegex(ValueError, "No original ScreenReaderSounds WAVs"):
            original_audio.add_screenreader_sounds(src, self.home / "not-created")
        self.assertFalse((self.home / "not-created").exists())

    def test_original_flat_screenreader_zip_nested_roles_ogg_fallback_and_keyboard(self):
        destination = self.home / "srs-merged"
        nested = io.BytesIO()
        with ZipFile(nested, "w") as archive:
            archive.writestr("objdata/button.wav", self.sample.read_bytes())
        src = self.home / "srs-audio.zip"
        different = self.home / "different.wav"
        make_wav(different, bits=8)
        with ZipFile(src, "w") as archive:
            archive.writestr("ScreenReaderSounds/button.wav", different.read_bytes())
            archive.writestr("ScreenReaderSounds/ShiftTab.wav", self.sample.read_bytes())
            archive.writestr("ScreenReaderSounds/paused_feedback.wav", self.sample.read_bytes())
            archive.writestr("ScreenReaderSounds/objdata.zip", nested.getvalue())
        report = original_audio.add_screenreader_sounds(src, destination)
        self.assertEqual(report["distinct_events"], 4)
        self.assertEqual((destination / "navigation/voiceover/role.button.wav").read_bytes(),
                         self.sample.read_bytes())
        self.assertTrue((destination / "keyboard/voiceover/keyboard.shift_tab.wav").is_file())
        self.assertTrue((destination / "navigation/voiceover/system.paused_feedback.wav").is_file())

    def test_old_zip_manifest_is_accepted_but_not_saved(self):
        zip_path = self.home / "old.zip"
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("theme.json", json.dumps({"name": "Old", "sounds": {
                "role.button": "sounds/click.wav", "key.space": "sounds/click.wav"}}))
            archive.writestr("sounds/click.wav", self.sample.read_bytes())
        nav = self.nav.import_zip(zip_path, "Old Navigation")
        typing = self.typing.import_zip(zip_path, "Old Keyboard")
        self.assertEqual(set(self.nav.load(nav)["sounds"]), {"role.button"})
        self.assertEqual(set(self.typing.load(typing)["sounds"]), {"key.space"})
        self.assertFalse((self.nav.directory(nav) / "theme.json").exists())

    def test_old_mixed_themes_migrate_non_destructively(self):
        old = self.home / "old-mixed" / "original"
        (old / "sounds").mkdir(parents=True)
        (old / "sounds" / "one.wav").write_bytes(self.sample.read_bytes())
        (old / "theme.json").write_text(json.dumps({"name": "ธีมส่วนตัว", "sounds": {
            "role.button": "sounds/one.wav", "key.character": "sounds/one.wav"}}), encoding="utf-8")
        self.assertEqual(self.nav.migrate_previous_themes(old.parent), 1)
        self.assertEqual(self.typing.migrate_previous_themes(old.parent), 1)
        nav = self.nav.load("user:ธีมส่วนตัว")["sounds"]
        typing = self.typing.load("user:ธีมส่วนตัว")["sounds"]
        self.assertEqual(set(nav), {"role.button"})
        self.assertEqual(set(typing), {"key.character"})
        self.assertTrue((old / "theme.json").exists())

    def test_v02_manifest_pack_migrates_with_full_backup(self):
        legacy = self.nav.writable / "mine"
        (legacy / "sounds").mkdir(parents=True)
        (legacy / "sounds" / "tone.wav").write_bytes(self.sample.read_bytes())
        (legacy / "theme.json").write_text(json.dumps({"name": "Mine", "sounds": {
            "system.lock": "sounds/tone.wav"}}), encoding="utf-8")
        self.assertEqual(self.nav.migrate_manifest_packs(), 1)
        self.assertIn("system.lock", self.nav.load("user:mine")["sounds"])
        self.assertFalse((legacy / "theme.json").exists())
        self.assertTrue((self.home / "soundThemes/legacy-backups" / "navigation" / "mine" / "theme.json").exists())

    def test_audio_cache_both_file_names_and_variations(self):
        fake = types.SimpleNamespace(_log=types.SimpleNamespace(warning=lambda *args: None))
        built = audio.AudioEngine._load_bank(fake, self.nav, "builtin:balanced", 50)
        self.assertEqual(len(built["system.lock"]), 1)
        theme = self.typing.create("Variant Pack")
        self.typing.assign(theme, "key.character", self.sample)
        self.typing.assign(theme, "key.character", self.sample, append=True)
        loaded = audio.AudioEngine._load_bank(fake, self.typing, theme, 50)
        self.assertEqual(len(loaded["key.character"]), 2)

    def test_random_typing_never_uses_navigation_or_unselected_typing_pack(self):
        nav = self.nav.create("Navigation")
        self.nav.assign(nav, "key.tab", self.sample)
        first = self.typing.create("Typing A")
        second = self.typing.create("Typing B")
        wav8 = self.home / "other.wav"
        make_wav(wav8, bits=8)
        self.typing.assign(first, "key.character", self.sample)
        self.typing.assign(first, "key.character", self.sample, append=True)
        self.typing.assign(second, "key.character", wav8)
        with self.assertRaises(ValueError):
            self.nav.assign(nav, "key.character", self.sample)
        with self.assertRaises(ValueError):
            self.typing.assign(first, "role.button", self.sample)
        fake = audio.AudioEngine.__new__(audio.AudioEngine)
        fake._log = types.SimpleNamespace(warning=lambda *args: None)
        fake._last_played = {}
        fake._queue = queue.Queue()
        fake._closed = threading.Event()
        audio.AudioEngine.reload(fake, self.nav, nav, self.typing, first, 100)
        for _ in range(30):
            audio.AudioEngine.play(fake, "key.character", min_gap=0)
        self.assertEqual({fake._queue.get_nowait()[0][1] for _ in range(30)}, {16})

    def test_runtime_roles_states_and_fallback_are_dynamic(self):
        example = types.SimpleNamespace(name="NEW_FUTURE_ROLE")
        dynamic = [entry[1] for entry in catalog.all_events([example], [example])]
        self.assertIn("role.newfuturerole", dynamic)
        self.assertIn("state.newfuturerole", dynamic)
        self.assertIn("role.default", catalog.candidates("role.newfuturerole"))

    def test_original_21_special_wav_names_have_events_and_trigger_sites(self):
        filenames = ("Tab ShiftTab clicked media scroll typekey typekeyspace typekeypr closed opened notext "
                     "collapsed expanded eclose delete lock lockscreen unlockscreen error end typekeyremove").split()
        source = "\n".join((PACKAGE_ROOT / path).read_text(encoding="utf-8")
                           for path in ("__init__.py", "browser.py", "keyboard_state.py"))
        for filename in filenames:
            event = catalog.legacy_event_for_filename(filename)
            self.assertIsNotNone(event, filename)
            self.assertIn('"' + event + '"', source, f"No trigger for {filename}.wav")

    def test_builtins_contain_only_real_source_wavs_without_synthetic_packs(self):
        effects = PACKAGE_ROOT / "effects"
        nav = packs.ThemeStore(effects / "navigation", self.home / "extra-nav", "navigation")
        typing = packs.ThemeStore(effects / "typing", self.home / "extra-type", "typing")
        keyboard = packs.ThemeStore(effects / "keyboard", self.home / "extra-keyboard", "keyboard")
        self.assertEqual({entry[0] for entry in nav.themes()},
                         {"builtin:default", "builtin:voiceover"})
        self.assertEqual({entry[0] for entry in typing.themes()},
                         {"builtin:voiceover", *(f"builtin:{p}" for p in effects_merge.TYPING_FOLDERS.values())})
        self.assertEqual({entry[0] for entry in keyboard.themes()},
                         {"builtin:voiceover", *(f"builtin:{p.lower()}" for p in kliq_audio.SETS)})
        navigation = nav.load("builtin:voiceover")["sounds"]
        keys = typing.load("builtin:classic-typewriter")["sounds"]
        self.assertEqual(len(navigation), 109)
        default_nav = nav.load("builtin:default")["sounds"]
        self.assertEqual(len(default_nav), 85)  # one duplicate editable-text alias
        for event in ("role.listitem", "role.tablecolumnheader", "role.tablerow",
                      "state.expanded", "state.invisible", "nav.caret"):
            self.assertIn(event, default_nav)
            self.assertIn(event, navigation)
        self.assertNotIn("role.tablecoulmnheader", default_nav)
        self.assertNotIn("role.tableraw", default_nav)
        for stale in ("role.activityindicator", "role.item", "role.on", "role.off"):
            self.assertNotIn(stale, default_nav)
            self.assertNotIn(stale, navigation)
        self.assertIn("role.tab", navigation)
        self.assertNotIn("key.tab", navigation)
        self.assertEqual(set(keys), {"key.character", "key.enter"})
        self.assertEqual(len(keys["key.character"]), 6)
        self.assertEqual(set(keyboard.load("builtin:voiceover")["sounds"]),
                         {"keyboard.backspace", "keyboard.end", "keyboard.shift_tab"})
        folders = [nav.directory("builtin:voiceover"), typing.directory("builtin:classic-typewriter"),
                   typing.directory("builtin:voiceover"), keyboard.directory("builtin:voiceover")]
        self.assertGreaterEqual(sum(len(list(folder.glob("*.wav"))) for folder in folders), 120)
        self.assertIn("nav.mouse", navigation)
        for name in kliq_audio.SETS:
            samples = keyboard.load("builtin:" + name.lower())["sounds"]
            self.assertIn("keyboard.a", samples)
            self.assertIn("keyboard.default", samples)
            self.assertGreaterEqual(len(samples), 55)
        self.assertTrue(all(not (folder / "theme.json").exists() for folder in folders))

    def test_effects_archive_fixes_real_nvda_names_and_keeps_typing_separate(self):
        cases = {
            "activity": "role.busyindicator",
            "item": "nav.selection",
            "on": "state.on",
            "off": "state.off",
            "tablecoulmnheader": "role.tablecolumnheader",
            "tableraw": "role.tablerow",
            "invisibled": "state.invisible",
            "expended": "state.expanded",
            "halfchecked": "state.halfchecked",
            "pressed": "state.pressed",
            "caret": "nav.caret",
            "complete": "system.complete",
            "listitem": "role.listitem",
        }
        for filename, event in cases.items():
            self.assertEqual(effects_merge.navigation_event(filename), event)
        self.assertEqual(effects_merge.typing_event("delete"), "key.backspace")
        self.assertEqual(effects_merge.typing_event("space"), "key.space")
        self.assertEqual(effects_merge.typing_event("typing_4"), "key.character")
        self.assertEqual(effects_merge.typing_event("bill"), "key.enter")
        self.assertIn("classic-typewriter", effects_merge.TYPING_FOLDERS.values())
        self.assertIn("state.off", catalog.EVENT_GROUPS["NVDA states"])
        self.assertIn('self.play_event("state.on" if on else "state.off")',
                      (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8"))

    def test_pcm_wav_formats_and_volume_scaling(self):
        for bits in (8, 16, 24, 32):
            path = self.home / f"sample-{bits}.wav"
            make_wav(path, bits)
            params, data = audio.decode_pcm(path, 50)
            self.assertEqual(params, (1, bits, 22050))
            self.assertEqual(len(data), bits // 8 * 4)
            packs.validate_wave(path)

    def test_k_style_key_tracker_uses_nvda_raw_keys_without_global_hook(self):
        keys = keys_module.KeyboardState()
        self.assertTrue(keys.update(0x10, True))  # Shift
        self.assertTrue(keys.update(0x09, True))  # Tab
        self.assertEqual(keys.event_for_key(0x09), "key.shift_tab")
        self.assertFalse(keys.update(0x09, True))  # Repeated keydown
        self.assertFalse(keys.update(0x09, False))
        self.assertFalse(keys.is_pressed(0x09))
        keys.update(0x10, False)
        self.assertEqual(keys.event_for_key(0xB3), "system.media")
        keys.clear()
        self.assertFalse(keys.is_pressed(0x10))

    def test_generic_shift_and_sided_shift_are_one_physical_key_event(self):
        keys = keys_module.KeyboardState()
        first, code = keys.update_physical(0x10, 0x2A, False, True)
        self.assertTrue(first)
        self.assertEqual(code, 0xA0)
        self.assertEqual(keyboard_catalog.event_for_virtual_key(code), "keyboard.left_shift")
        first, code = keys.update_physical(0xA0, 0x2A, False, True)
        self.assertFalse(first)  # duplicate report must not play another WAV
        self.assertEqual(code, 0xA0)
        self.assertTrue(keys.is_pressed(0x10))
        self.assertFalse(keys.update_physical(0x10, 0x2A, False, False)[0])
        self.assertFalse(keys.is_pressed(0x10))
        self.assertTrue(keys.update_physical(0xA0, 0x2A, False, True)[0])
        keys.update_physical(0xA0, 0x2A, False, False)
        self.assertTrue(keys.update_physical(0x10, 0x36, False, True)[0])
        self.assertTrue(keys.is_pressed(0x10))
        self.assertEqual(keys_module.physical_virtual_key(0x10, 0x36), 0xA1)
        self.assertEqual(keys_module.physical_virtual_key(0x11, extended=True), 0xA3)
        self.assertEqual(keys_module.physical_virtual_key(0x12, extended=True), 0xA5)
        # Left and right Shift really can be held independently.
        self.assertTrue(keys.update_physical(0x10, 0x2A, False, True)[0])

    def test_speech_pause_caused_by_shift_is_not_a_second_keyboard_sound(self):
        keys = keys_module.KeyboardState()
        self.assertFalse(keys.shift_recent())
        keys.update_physical(0x10, 0x2A, False, True)
        self.assertTrue(keys.shift_recent())
        keys.update_physical(0x10, 0x2A, False, False)
        self.assertTrue(keys.shift_recent())  # async speech callback can arrive after keyup
        with patch.object(keys_module.time, "monotonic", return_value=time.monotonic() + 1):
            self.assertFalse(keys.shift_recent())
        keys.clear()
        self.assertFalse(keys.shift_recent())

        plugin = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('"pauseFeedback": "boolean(default=false)"', plugin)
        callback = plugin.split("def _speech_paused", 1)[1].split("def _startup", 1)[0]
        self.assertIn('self.setting("pauseFeedback")', callback)
        self.assertIn('not self.keys.shift_recent()', callback)
        self.assertIn('not _pressed(0x10)', callback)

        # Run the actual NVDA-independent callback body with a stub plugin;
        # don't rely solely on matching its source text.
        parsed = ast.parse(plugin)
        class_node = next(node for node in parsed.body
                          if isinstance(node, ast.ClassDef) and node.name == "GlobalPlugin")
        callback_node = next(node for node in class_node.body
                             if isinstance(node, ast.FunctionDef) and node.name == "_speech_paused")
        environment = {"_pressed": lambda vk: False}
        exec(compile(ast.Module(body=[callback_node], type_ignores=[]), "<pause-test>", "exec"),
             environment)
        played = []
        stub = types.SimpleNamespace(
            keys=keys_module.KeyboardState(),
            setting=lambda option: True,
            play_event=lambda *args: played.append(args),
        )
        stub.keys.update_physical(0x10, 0x2A, False, True)
        environment["_speech_paused"](stub, True)
        self.assertEqual(played, [])
        stub.keys.clear()
        environment["_speech_paused"](stub, True)
        self.assertEqual(played, [("system.paused_feedback", 0)])
        stub.setting = lambda option: False
        environment["_speech_paused"](stub, True)
        self.assertEqual(len(played), 1)

    def test_all_sound_events_have_accessible_contextual_descriptions(self):
        for group, event_key, label in catalog.all_events(
                [types.SimpleNamespace(name="LISTITEM"), types.SimpleNamespace(name="CHIP")],
                [types.SimpleNamespace(name="SELECTED")]):
            description = catalog.event_description(event_key, label)
            self.assertTrue(description.strip(), (group, event_key))
            self.assertNotEqual(description, label)
        for _, event_key, label in keyboard_catalog.all_keyboard_events():
            self.assertTrue(catalog.event_description(event_key, label).strip())
        self.assertIn("File Explorer", catalog.event_description("role.listitem", "LISTITEM"))
        self.assertIn("browser", catalog.event_description("role.tab", "TAB"))
        self.assertIn("Shift", catalog.event_description("system.paused_feedback"))
        self.assertIn("physical left shift", catalog.event_description("keyboard.left_shift", "Left Shift").lower())
        self.assertIn("File Explorer", catalog.event_description("role.listitem", "LISTITEM", "th_TH"))
        self.assertIn("Shift", catalog.event_description("system.paused_feedback", language="th"))
        self.assertIn("ปุ่ม", catalog.event_description("keyboard.c", "C", "th"))
        self.assertEqual(set(catalog.EVENT_DESCRIPTIONS), set(catalog.TH_EVENT_DESCRIPTIONS))

    def test_event_description_is_announced_separately_without_changing_search_names(self):
        editor = (PACKAGE_ROOT / "settings.py").read_text(encoding="utf-8")
        self.assertIn("self.events.Set([name for key, name in self.visible])", editor)
        self.assertIn("self.event_help.SetValue(explanation)", editor)
        self.assertIn("languageHandler.getLanguage()", editor)
        self.assertIn("self.announce_help.GetValue()", editor)
        self.assertIn("ui.message(explanation)", editor)
        self.assertIn("wx.CallLater(170, self._announce_event", editor)
        self.assertIn("self.events.Bind(wx.EVT_LISTBOX, self.on_select)", editor)

    def test_key_catalog_distinct_events_for_every_windows_vk(self):
        entries = keyboard_catalog.all_keyboard_events()
        names = {event for _, event, _ in entries}
        self.assertGreaterEqual(len(names), 255)
        for vk in range(1, 256):
            self.assertIn(keyboard_catalog.event_for_virtual_key(vk), names)
        samples = {0x09: "keyboard.tab", 0x24: "keyboard.home", 0x23: "keyboard.end",
                   0x21: "keyboard.pageup", 0x22: "keyboard.pagedown", 0x13: "keyboard.pause",
                   0x70: "keyboard.f1", 0x7B: "keyboard.f12", 0x41: "keyboard.a",
                   0x5A: "keyboard.z", 0xAD: "keyboard.volume_mute", 0x14: "keyboard.capslock"}
        for vk, expected in samples.items():
            self.assertEqual(keyboard_catalog.event_for_virtual_key(vk), expected)
        self.assertEqual(keyboard_catalog.event_for_virtual_key(0x11, extended=True), "keyboard.right_ctrl")
        self.assertEqual(keyboard_catalog.event_for_virtual_key(0x10, scan_code=0x36), "keyboard.right_shift")
        self.assertEqual(keyboard_catalog.event_for_virtual_key(0x0D, extended=True), "keyboard.numpad_enter")
        self.assertIn("keyboard.brightness_down", names)
        self.assertIn("keyboard.shift_tab", names)

    def test_keyboard_sound_mode_is_exclusive_but_normal_modes_can_coexist(self):
        self.assertEqual(modes.resolve_modes(True, True, False), (True, True, False))
        self.assertEqual(modes.resolve_modes(True, True, True, "keyboard"), (False, False, True))
        self.assertEqual(modes.resolve_modes(True, False, True, "navigation"), (True, False, False))
        self.assertEqual(modes.resolve_modes(False, True, True, "typing"), (False, True, False))

    def test_keyboard_theme_exact_wav_renaming_isolated_from_typing_randomness(self):
        keys = self.keyboard.create("Custom Mechvibes")
        self.assertEqual(self.keyboard.load(keys)["sounds"], {})
        self.keyboard.assign(keys, "keyboard.a", self.sample)
        self.assertTrue((self.keyboard.directory(keys) / "keyboard.a.wav").is_file())
        self.assertEqual(self.keyboard.sound_for(keys, "keyboard.a").name, "keyboard.a.wav")
        self.assertIsNone(self.keyboard.sound_for(keys, "keyboard.b"))
        with self.assertRaises(ValueError):
            self.keyboard.assign(keys, "keyboard.a", self.sample, append=True)
        for event in ("key.character", "role.button", "key.tab"):
            with self.assertRaises(ValueError):
                self.keyboard.assign(keys, event, self.sample)
        self.assertFalse(self.typing.accepts("keyboard.a"))
        self.assertFalse(self.nav.accepts("keyboard.a"))
        zip_path = self.home / "key-pack.zip"
        self.keyboard.export_zip(keys, zip_path)
        imported = self.keyboard.import_zip(zip_path, "Reimport Key Pack")
        self.assertIn("keyboard.a", self.keyboard.load(imported)["sounds"])

    def test_preview_pack_chooses_one_real_in_pack_recording(self):
        effects = PACKAGE_ROOT / "effects"
        nav = packs.ThemeStore(effects / "navigation", self.home / "nav-preview", "navigation")
        typing = packs.ThemeStore(effects / "typing", self.home / "typing-preview", "typing")
        keyboard = packs.ThemeStore(effects / "keyboard", self.home / "keyboard-preview", "keyboard")
        self.assertEqual(nav.preview_sound("builtin:voiceover").name, "role.listitem.wav")
        self.assertTrue(typing.preview_sound("builtin:classic-typewriter").name.startswith("key.character"))
        self.assertEqual(keyboard.preview_sound("builtin:cherry").name, "keyboard.a.wav")
        self.assertIsNone(keyboard.preview_sound("user:nonexistent"))
        personal = keyboard.create("Sparse Pack")
        keyboard.assign(personal, "keyboard.f7", self.sample)
        self.assertEqual(keyboard.preview_sound(personal).name, "keyboard.f7.wav")

    def test_sound_lists_have_first_letter_search_labels_and_select_to_preview(self):
        panel = (PACKAGE_ROOT / "settings.py").read_text(encoding="utf-8")
        self.assertIn("self.theme_list.Set([name for _, name in self.choices])", panel)
        self.assertIn("self.theme_list.Bind(wx.EVT_LISTBOX, self.on_theme_selection)", panel)
        self.assertIn("self.events.Bind(wx.EVT_LISTBOX, self.on_select)", panel)
        self.assertIn("self.events.Set([name for key, name in self.visible])", panel)
        self.assertGreaterEqual(panel.count("self.preview_setting_theme("), 3)
        self.assertEqual([label for _, key, label in keyboard_catalog.all_keyboard_events()
                          if key == "keyboard.c"], ["C"])
        future = types.SimpleNamespace(name="CHIP")
        self.assertIn(("NVDA roles", "role.chip", "CHIP"), catalog.all_events([future], []))

    def test_rapid_preview_selection_skips_outdated_decoding_without_blocking_ui(self):
        slow_started = threading.Event()
        release_old = threading.Event()
        preview_played = threading.Event()
        heard = []
        latest_file = self.home / "latest.wav"
        make_wav(latest_file)

        def delayed_decode(path, volume):
            if path == self.sample:
                slow_started.set()
                release_old.wait(2)
                return (1, 16, 22050), b"old"
            return (1, 16, 22050), b"latest"

        class FakeWavePlayer:
            def __init__(self, **kwargs):
                pass

            def feed(self, raw):
                heard.append(raw)
                preview_played.set()

            def idle(self):
                pass

            def close(self):
                pass

        logger = types.SimpleNamespace(warning=lambda *args: None)
        with patch.dict(sys.modules, {"nvwave": types.SimpleNamespace(WavePlayer=FakeWavePlayer)}), \
                patch.object(audio, "decode_pcm", delayed_decode):
            engine = audio.AudioEngine(lambda: "device", logger)
            try:
                engine.preview_file(self.sample, 100)
                self.assertTrue(slow_started.wait(2))
                started = time.monotonic()
                engine.preview_file(latest_file, 100)
                self.assertLess(time.monotonic() - started, 0.05)
                release_old.set()
                self.assertTrue(preview_played.wait(2))
                self.assertEqual(heard, [b"latest"])
            finally:
                release_old.set()
                engine.close()

    def test_keyboard_pack_never_randomizes_and_unknown_files_are_ignored(self):
        theme = self.keyboard.create("Fixed Keys")
        folder = self.keyboard.directory(theme)
        (folder / "a.wav").write_bytes(self.sample.read_bytes())
        (folder / "random-click.wav").write_bytes(self.sample.read_bytes())
        self.assertEqual(self.keyboard.load(theme)["sounds"], {"keyboard.a": "a.wav"})
        second = self.home / "second.wav"
        make_wav(second, bits=8)
        self.keyboard.assign(theme, "keyboard.a", second)
        fake = audio.AudioEngine.__new__(audio.AudioEngine)
        fake._log = types.SimpleNamespace(warning=lambda *args: None)
        fake._last_played = {}
        fake._queue = queue.Queue()
        fake._closed = threading.Event()
        audio.AudioEngine.reload(fake, self.nav, "builtin:balanced", self.typing, "", 100,
                                 self.keyboard, theme)
        for _ in range(8):
            audio.AudioEngine.play(fake, "keyboard.a", min_gap=0)
        self.assertEqual([fake._queue.get_nowait()[0][1] for _ in range(8)], [8] * 8)

    def test_real_kliq_keydown_import_without_unused_keyup_files(self):
        zip_path = self.home / "sounds.zip"
        with ZipFile(zip_path, "w") as archive:
            for pack in kliq_audio.SETS:
                archive.writestr(f"Sounds/{pack}/30-down.wav", self.sample.read_bytes())
                archive.writestr(f"Sounds/{pack}/30-up.wav", self.sample.read_bytes())
        summary = kliq_audio.import_kliq(zip_path, self.home / "built-effects")
        self.assertEqual(summary, {pack.lower(): 2 for pack in kliq_audio.SETS})
        for pack in kliq_audio.SETS:
            directory = self.home / "built-effects/keyboard" / pack.lower()
            self.assertEqual({p.name for p in directory.glob("*.wav")},
                             {"keyboard.a.wav", "keyboard.default.wav"})
        self.assertEqual(kliq_audio.SCAN_EVENTS[59], "f1")
        self.assertEqual(kliq_audio.SCAN_EVENTS[57416], "up")

    def test_focus_selection_in_file_explorer_uses_real_item_role_not_missing_state(self):
        item = types.SimpleNamespace(name="LISTITEM")
        selected = types.SimpleNamespace(name="SELECTED")
        self.assertEqual(focus_policy.cue_for_focus(item, [selected], lambda event: False),
                         "role.listitem")
        expanded = types.SimpleNamespace(name="EXPANDED")
        self.assertEqual(focus_policy.cue_for_focus(item, [expanded], lambda event: event == "state.expanded"),
                         "state.expanded")

    def test_real_keyboard_fallback_never_leaks_from_other_sound_categories(self):
        self.assertEqual(catalog.candidates("keyboard.f13"),
                         ("keyboard.f13", "keyboard.default"))
        self.assertEqual(catalog.candidates("keyboard.shift_tab"),
                         ("keyboard.shift_tab", "keyboard.tab", "keyboard.default"))
        self.assertNotIn("nav.focus", catalog.candidates("keyboard.f13"))
        self.assertEqual(catalog.candidates("keyboard.default"), ("keyboard.default",))

    def test_rapid_focus_updates_replace_stale_audio(self):
        fake = audio.AudioEngine.__new__(audio.AudioEngine)
        fake._last_played = {}
        fake._queue = queue.Queue(maxsize=1)
        fake._closed = threading.Event()
        fake._sounds = {
            "role.button": [((1, 16, 22050), b"old")],
            "role.listitem": [((1, 16, 22050), b"new")],
        }
        fake._typing_sounds = {}
        fake._keyboard_sounds = {}
        audio.AudioEngine.play(fake, "role.button", 0)
        audio.AudioEngine.play(fake, "role.listitem", 0)
        self.assertEqual(fake._queue.get_nowait()[1], b"new")

    def test_multiple_long_effects_play_simultaneously_without_interrupting(self):
        """Navigation, typing and keyboard audio use distinct running streams."""
        release = threading.Event()
        all_started = threading.Event()
        lock = threading.Lock()
        started = []
        instances = []

        class FakePlayer:
            def __init__(self, **kwargs):
                self.stopped = False
                instances.append(self)

            def feed(self, data):
                with lock:
                    started.append(data)
                    if len(started) == 3:
                        all_started.set()

            def idle(self):
                # Simulate a long file: the first sound has NOT finished when
                # the other two begin, and no earlier player may be stopped.
                release.wait(2)

            def close(self):
                self.stopped = True

            def stop(self):
                self.stopped = True

        fake_nvwave = types.SimpleNamespace(WavePlayer=FakePlayer)
        logger = types.SimpleNamespace(warning=lambda *args: None)
        with patch.dict(sys.modules, {"nvwave": fake_nvwave}):
            engine = audio.AudioEngine(lambda: "test-device", logger)
            try:
                engine._sounds = {"role.button": [((1, 16, 22050), b"navigation")]}
                engine._typing_sounds = {"key.character": [((1, 16, 22050), b"typing")]}
                engine._keyboard_sounds = {"keyboard.a": [((1, 16, 22050), b"keyboard")]}
                for event in ("role.button", "key.character", "keyboard.a"):
                    engine.play(event, min_gap=0)
                self.assertTrue(all_started.wait(2), "A long WAV delayed a second audio category")
                self.assertEqual(set(started), {b"navigation", b"typing", b"keyboard"})
                self.assertEqual(len(instances), 3)
                self.assertFalse(any(instance.stopped for instance in instances))
            finally:
                release.set()
                engine.close()

    def test_bounded_polyphony_drops_stale_waiting_cues_instead_of_blocking(self):
        release = threading.Event()
        all_busy = threading.Event()
        count = [0]
        lock = threading.Lock()

        class FakePlayer:
            def __init__(self, **kwargs):
                pass

            def feed(self, data):
                with lock:
                    count[0] += 1
                    if count[0] == audio.AudioEngine.MAX_VOICES:
                        all_busy.set()

            def idle(self):
                release.wait(2)

            def close(self):
                pass

            def stop(self):
                pass

        logger = types.SimpleNamespace(warning=lambda *args: None)
        with patch.dict(sys.modules, {"nvwave": types.SimpleNamespace(WavePlayer=FakePlayer)}):
            engine = audio.AudioEngine(lambda: "device", logger)
            try:
                engine._sounds = {"role.button": [((1, 16, 22050), b"click")]}
                for _ in range(audio.AudioEngine.MAX_VOICES):
                    engine.play("role.button", min_gap=0)
                self.assertTrue(all_busy.wait(2))
                start = time.monotonic()
                for _ in range(500):
                    engine.play("role.button", min_gap=0)
                self.assertLess(time.monotonic() - start, 1.0)
                self.assertLessEqual(engine._queue.qsize(), audio.AudioEngine.MAX_VOICES)
                self.assertEqual(len(engine._voices), audio.AudioEngine.MAX_VOICES)
            finally:
                release.set()
                engine.close()

    def test_keyboard_navigation_cues_only_activate_in_keyboard_mode(self):
        plugin = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('if first and not self._closed and self.setting("keyboard")', plugin)
        focus_block = plugin.split("def event_gainFocus", 1)[1].split("def event_typedCharacter", 1)[0]
        self.assertNotIn("self.play_event(key)", focus_block)
        self.assertIn('self.play_event("nav.scroll")', focus_block)
        self.assertIn('event_for_virtual_key(physical_vk, scanCode, extended)', plugin)
        self.assertIn('self.keys.update_physical(', plugin)

    def test_session_lock_secure_desktop_raw_input_and_mouse_sites(self):
        plugin = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("post_sessionLockStateChanged", plugin)
        self.assertIn("post_secureDesktopStateChange", plugin)
        self.assertIn("decide_handleRawKey", plugin)
        self.assertIn("event_mouseMove", plugin)
        self.assertIn("hoverDelay", plugin)
        self.assertIn("self._browse_monitor.patch()", plugin)
        self.assertNotIn("self._register(visionHandlerExtensionPoints.post_browseModeMove", plugin)
        self.assertIn("post_speechPaused", plugin)
        self.assertIn('self.play_event("system.paused_feedback", 0)', plugin)


if __name__ == "__main__":
    unittest.main()
