"""Regression suite for NVDA-independent sound packs and keyboard context."""

from __future__ import annotations

import importlib
import importlib.util
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
        self.assertEqual([entry[0] for entry in nav.themes()], ["builtin:voiceover"])
        self.assertEqual([entry[0] for entry in typing.themes()],
                         ["builtin:classic-typewriter", "builtin:voiceover"])
        self.assertEqual({entry[0] for entry in keyboard.themes()},
                         {"builtin:voiceover", *(f"builtin:{p.lower()}" for p in kliq_audio.SETS)})
        navigation = nav.load("builtin:voiceover")["sounds"]
        keys = typing.load("builtin:classic-typewriter")["sounds"]
        self.assertEqual(len(navigation), 50)
        self.assertIn("role.tab", navigation)
        self.assertNotIn("key.tab", navigation)
        self.assertEqual(set(keys), {"key.character"})
        self.assertEqual(len(keys["key.character"]), 6)
        self.assertEqual(set(keyboard.load("builtin:voiceover")["sounds"]),
                         {"keyboard.backspace", "keyboard.end", "keyboard.shift_tab"})
        folders = [nav.directory("builtin:voiceover"), typing.directory("builtin:classic-typewriter"),
                   typing.directory("builtin:voiceover"), keyboard.directory("builtin:voiceover")]
        self.assertEqual(sum(len(list(folder.glob("*.wav"))) for folder in folders), 63)
        self.assertIn("nav.mouse", navigation)
        for name in kliq_audio.SETS:
            samples = keyboard.load("builtin:" + name.lower())["sounds"]
            self.assertIn("keyboard.a", samples)
            self.assertIn("keyboard.default", samples)
            self.assertGreaterEqual(len(samples), 55)
        self.assertTrue(all(not (folder / "theme.json").exists() for folder in folders))

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
        self.assertIn('event_for_virtual_key(vkCode, scanCode, extended)', plugin)

    def test_session_lock_secure_desktop_raw_input_and_mouse_sites(self):
        plugin = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("post_sessionLockStateChanged", plugin)
        self.assertIn("post_secureDesktopStateChange", plugin)
        self.assertIn("decide_handleRawKey", plugin)
        self.assertIn("event_mouseMove", plugin)
        self.assertIn("hoverDelay", plugin)
        self.assertIn("post_browseModeMove", plugin)
        self.assertIn("post_speechPaused", plugin)
        self.assertIn('self.play_event("system.paused_feedback", 0)', plugin)


if __name__ == "__main__":
    unittest.main()
