"""Build the standard NVDA add-on ZIP package. Run from any directory."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
VERSION = next(line.split('"')[1] for line in (ROOT / "manifest.ini").read_text(encoding="utf-8").splitlines()
               if line.startswith("version = "))
DESTINATION = ROOT / f"SoundThemesForNVDA-{VERSION}.nvda-addon"
INCLUDE = ("manifest.ini", "globalPlugins", "doc")


def build():
    with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=7) as archive:
        for entry in INCLUDE:
            path = ROOT / entry
            if path.is_file():
                archive.write(path, entry)
            else:
                for candidate in sorted(path.rglob("*")):
                    if candidate.is_file() and candidate.suffix not in (".pyc", ".tmp") and "__pycache__" not in candidate.parts:
                        archive.write(candidate, candidate.relative_to(ROOT).as_posix())
    print(f"Created {DESTINATION} ({DESTINATION.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
