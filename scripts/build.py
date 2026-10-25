"""Build the standard NVDA add-on ZIP package. Run from any directory."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
VERSION = next(line.split('"')[1] for line in (ROOT / "manifest.ini").read_text(encoding="utf-8").splitlines()
               if line.startswith("version = "))
DESTINATION = ROOT / f"SoundThemesForNVDA-{VERSION}.nvda-addon"
INCLUDE = ("manifest.ini", "installTasks.py", "globalPlugins", "doc", "locale")
STOCK_MANIFEST = "soundthemes-stock-wavs.json"
EFFECTS = ROOT / "globalPlugins" / "soundThemes" / "effects"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build():
    with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=7) as archive:
        original_wavs = {}
        for entry in INCLUDE:
            path = ROOT / entry
            if path.is_file():
                archive.write(path, entry)
            else:
                for candidate in sorted(path.rglob("*")):
                    if candidate.is_file() and candidate.suffix not in (".pyc", ".tmp") and "__pycache__" not in candidate.parts:
                        archive.write(candidate, candidate.relative_to(ROOT).as_posix())
                        if candidate.is_relative_to(EFFECTS) and candidate.suffix.lower() == ".wav":
                            original_wavs[candidate.relative_to(EFFECTS).as_posix()] = _sha256(candidate)
        # This is the baseline of the shipped stock sounds, *before* NVDA's
        # installTasks merges in a user's modified WAVs. Later updates can
        # preserve edits while still receiving new untouched factory sounds.
        archive.writestr(STOCK_MANIFEST, json.dumps({
            "schema": 1, "files": original_wavs,
        }, sort_keys=True, separators=(",", ":")))
    print(f"Created {DESTINATION} ({DESTINATION.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
