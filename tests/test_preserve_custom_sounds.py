"""Run installation-time personalized WAV preservation without NVDA/wx."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = module_from(ROOT / "installTasks.py", "soundThemesInstallTasksUnderTest")


class PreserveUserSoundsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root / "soundThemes"
        self.new = self.root / "soundThemes.pendingInstall"
        self.old_effects = self.old / installer.EFFECTS
        self.new_effects = self.new / installer.EFFECTS
        self.new_effects.mkdir(parents=True)

    def wav(self, base, path, value):
        target = base / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
        return target

    def manifest(self, entries):
        self.old.mkdir(parents=True, exist_ok=True)
        (self.old / installer.STOCK_MANIFEST).write_text(json.dumps({
            "schema": 1, "files": {
                path: hashlib.sha256(value).hexdigest()
                for path, value in entries.items()
            },
        }), encoding="utf-8")

    def test_first_upgrade_without_manifest_protects_all_old_wavs(self):
        path = "navigation/voiceover/role.button.wav"
        self.wav(self.old_effects, path, b"personal edit made in old NVDA addon")
        self.wav(self.new_effects, path, b"new stock file")
        self.wav(self.new_effects, "navigation/voiceover/role.menu.wav", b"new feature")
        self.wav(self.old_effects, "keyboard/my-pack/keyboard.a.wav", b"a custom theme")

        result = installer.preserve_personal_wavs(self.old, self.new)
        self.assertEqual(result["copied"], 2)
        self.assertEqual((self.new_effects / path).read_bytes(), b"personal edit made in old NVDA addon")
        self.assertEqual((self.new_effects / "navigation/voiceover/role.menu.wav").read_bytes(),
                         b"new feature")
        self.assertEqual((self.new_effects / "keyboard/my-pack/keyboard.a.wav").read_bytes(),
                         b"a custom theme")
        self.assertEqual((self.old_effects / path).read_bytes(), b"personal edit made in old NVDA addon")

    def test_known_baseline_preserves_edits_and_receives_new_factory_wavs(self):
        same = "navigation/voiceover/role.button.wav"
        changed = "navigation/voiceover/role.link.wav"
        deleted = "navigation/voiceover/role.checkbox.wav"
        self.manifest({same: b"original button", changed: b"original link", deleted: b"deleted stock"})
        self.wav(self.old_effects, same, b"original button")
        self.wav(self.old_effects, changed, b"my link sound")
        self.wav(self.old_effects, "navigation/voiceover/_unused/removed.wav", b"my hidden old cue")
        self.wav(self.new_effects, same, b"updated factory button")
        self.wav(self.new_effects, changed, b"updated factory link")
        self.wav(self.new_effects, deleted, b"factory restored checkbox")
        self.wav(self.new_effects, "navigation/voiceover/role.menu.wav", b"new factory menu")

        report = installer.preserve_personal_wavs(self.old, self.new)
        self.assertEqual(report, {"copied": 2, "kept_new_stock": 1, "deleted": 1,
                                  "removed_packs": 0})
        self.assertEqual((self.new_effects / same).read_bytes(), b"updated factory button")
        self.assertEqual((self.new_effects / changed).read_bytes(), b"my link sound")
        self.assertFalse((self.new_effects / deleted).exists())
        self.assertEqual((self.new_effects / "navigation/voiceover/role.menu.wav").read_bytes(),
                         b"new factory menu")
        self.assertEqual((self.new_effects / "navigation/voiceover/_unused/removed.wav").read_bytes(),
                         b"my hidden old cue")

    def test_deleted_complete_preset_stays_absent_without_hiding_new_packs(self):
        removed_pack_file = "navigation/voiceover/role.button.wav"
        other_pack_file = "navigation/classic/role.button.wav"
        new_pack_file = "navigation/new-pack/role.button.wav"
        self.manifest({removed_pack_file: b"original", other_pack_file: b"still here"})
        # The user removed voiceover entirely but retained classic.
        self.wav(self.old_effects, other_pack_file, b"still here")
        self.wav(self.new_effects, removed_pack_file, b"new voiceover factory audio")
        self.wav(self.new_effects, "navigation/voiceover/role.menu.wav", b"new cue in removed pack")
        self.wav(self.new_effects, other_pack_file, b"new classic factory audio")
        self.wav(self.new_effects, new_pack_file, b"new factory pack")

        # NVDA preferences are stored in the user's config, outside the add-on.
        preferences = self.root / "nvda.ini"
        preferences.write_text("[soundThemes]\nremovedNavigationPresets=['voiceover']\n"
                               "volume=37\n", encoding="utf-8")
        unchanged_preferences = preferences.read_bytes()
        report = installer.preserve_personal_wavs(self.old, self.new)
        self.assertEqual(report["removed_packs"], 1)
        self.assertFalse((self.new_effects / "navigation/voiceover").exists())
        self.assertEqual((self.new_effects / other_pack_file).read_bytes(),
                         b"new classic factory audio")
        self.assertEqual((self.new_effects / new_pack_file).read_bytes(), b"new factory pack")
        self.assertEqual(preferences.read_bytes(), unchanged_preferences)

    def test_on_install_uses_previous_addon_next_to_pending_install(self):
        path = "typing/classic-typewriter/key.enter.wav"
        self.wav(self.old_effects, path, b"personal")
        self.wav(self.new_effects, path, b"stock")
        with mock.patch.object(installer, "__file__", str(self.new / "installTasks.py")):
            installer.onInstall()
        self.assertEqual((self.new_effects / path).read_bytes(), b"personal")

    def test_clean_install_and_unrelated_code_never_create_sound_folders(self):
        self.assertEqual(installer.preserve_personal_wavs(self.old, self.new)["copied"], 0)
        with mock.patch.object(installer, "__file__", str(self.root / "randomFolder/installTasks.py")):
            installer.onInstall()
        self.assertFalse((self.old / installer.EFFECTS).exists())

    def test_update_aborts_on_failed_copy_instead_of_losing_personal_wav(self):
        path = "keyboard/old-custom/keyboard.space.wav"
        self.wav(self.old_effects, path, b"irreplaceable edit")
        self.wav(self.new_effects, path, b"new stock")
        with mock.patch.object(installer.shutil, "copy2", side_effect=PermissionError("locked WAV")):
            with self.assertRaises(PermissionError):
                installer.preserve_personal_wavs(self.old, self.new)
        self.assertEqual((self.old_effects / path).read_bytes(), b"irreplaceable edit")
        self.assertEqual((self.new_effects / path).read_bytes(), b"new stock")

    def test_update_missing_sounds_directory_does_not_discard_existing_packs(self):
        path = "navigation/voiceover/role.button.wav"
        self.wav(self.old_effects, path, b"personal")
        pending_without_effects = self.root / "incomplete.pendingInstall"
        pending_without_effects.mkdir()
        with self.assertRaises(FileNotFoundError):
            installer.preserve_personal_wavs(self.old, pending_without_effects)
        self.assertEqual((self.old_effects / path).read_bytes(), b"personal")

    def test_builder_bundles_install_hook_and_unmodified_stock_hash_manifest(self):
        builder = module_from(ROOT / "scripts" / "build.py", "soundThemesBuilderUnderTest")
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            (temp / "manifest.ini").write_text('version = "0.17.4"', encoding="utf-8")
            (temp / "installTasks.py").write_text("def onInstall(): pass\n", encoding="utf-8")
            wav = temp / "globalPlugins/soundThemes/effects/typing/preset/key.a.wav"
            wav.parent.mkdir(parents=True)
            wav.write_bytes(b"shipped WAV")
            builder.ROOT = temp
            builder.EFFECTS = temp / "globalPlugins/soundThemes/effects"
            builder.DESTINATION = temp / "test.nvda-addon"
            builder.build()
            with ZipFile(builder.DESTINATION) as archive:
                self.assertIn("installTasks.py", archive.namelist())
                hashes = json.loads(archive.read(installer.STOCK_MANIFEST))
                self.assertEqual(hashes["files"], {
                    "typing/preset/key.a.wav": hashlib.sha256(b"shipped WAV").hexdigest(),
                })


if __name__ == "__main__":
    unittest.main()
