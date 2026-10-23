"""Create the complete GitHub-ready source archive with all genuine WAVs."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = next(
    line.split('"')[1]
    for line in (ROOT / "manifest.ini").read_text(encoding="utf-8").splitlines()
    if line.startswith("version = ")
)
DESTINATION = ROOT.parent / f"SoundThemesForNVDA-source-{VERSION}.zip"
OMIT_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
OMIT_SUFFIXES = {".pyc", ".tmp", ".nvda-addon"}


def build():
    with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=7) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(piece in OMIT_DIRS for piece in rel.parts) or path.suffix in OMIT_SUFFIXES:
                continue
            archive.write(path, (Path("soundThemes") / rel).as_posix())
    print(f"Created {DESTINATION} ({DESTINATION.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
