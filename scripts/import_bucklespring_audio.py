"""Convert official Bucklespring's real per-key WAVs to an NVDA keyboard pack.

Usage: python scripts/import_bucklespring_audio.py upload/bucklespring-master.zip

Bucklespring (c) Ico Doornekamp, GNU GPL v2. The source uses `NN-1.wav`
for key DOWN and `NN-0.wav` for key UP, see zevv/bucklespring main.c.
This importer performs only lossless copying, not sample generation.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from zipfile import ZipFile

from import_kliq_audio import EFFECTS, SCAN_EVENTS, _validate


_MEMBER = re.compile(r"^bucklespring-master/wav/([0-9a-fA-F]{2})-([01])\.wav$")
_EXTRA = {
    0x45: "numlock", 0x46: "scrolllock", 0x47: "numpad_7",
    0x48: "numpad_8", 0x49: "numpad_9", 0x4A: "subtract",
    0x4B: "numpad_4", 0x4C: "numpad_5", 0x4D: "numpad_6",
    0x4E: "add", 0x4F: "numpad_1", 0x50: "numpad_2",
    0x51: "numpad_3", 0x52: "numpad_0", 0x53: "decimal",
    0x56: "oem_102", 0x57: "f11", 0x58: "f12",
    0x5B: "ime_kana",
    # Linux evdev key codes for the extended key block used by Bucklespring.
    0x60: "numpad_enter", 0x61: "right_ctrl", 0x62: "divide",
    0x63: "printscreen", 0x64: "right_alt", 0x66: "home",
    0x67: "up", 0x68: "pageup", 0x69: "left", 0x6A: "right",
    0x6B: "end", 0x6C: "down", 0x6D: "pagedown",
    0x6E: "insert", 0x6F: "delete", 0x77: "pause",
    0x7D: "left_windows",
    0xFF: "default",
}


def import_bucklespring(source: Path, destination: Path = EFFECTS) -> dict[str, int]:
    source = Path(source)
    samples = {}
    skipped = set()
    with ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) > 350 or sum(entry.file_size for entry in infos) > 30_000_000:
            raise ValueError("Unexpectedly large Bucklespring archive")
        corrupted = archive.testzip()
        if corrupted:
            raise ValueError(f"Damaged Bucklespring WAV: {corrupted}")
        for member in infos:
            match = _MEMBER.fullmatch(member.filename)
            if not match:
                continue
            key = int(match.group(1), 16)
            name = SCAN_EVENTS.get(key) or _EXTRA.get(key)
            if name is None:
                skipped.add(key)
                continue
            # Bucklespring's C source: int idx = code + press * 256, and
            # snprintf(..., "%02x-%d.wav", ..., code, press).
            is_down = match.group(2) == "1"
            event = "keyboard." + name
            filename = (f"{event}.wav" if is_down else f"{event}__release.wav")
            audio = archive.read(member)
            _validate(audio, member.filename)
            samples.setdefault(filename, audio)
    if "keyboard.a.wav" not in samples or "keyboard.default.wav" not in samples:
        raise ValueError("Bucklespring source lacks its real key-down WAV samples")
    folder = Path(destination) / "keyboard" / "bucklespring"
    folder.mkdir(parents=True, exist_ok=True)
    for filename, audio in samples.items():
        (folder / filename).write_bytes(audio)
    return {"recordings": len(samples), "unmapped_scan_codes": len(skipped)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--destination", type=Path, default=EFFECTS)
    args = parser.parse_args()
    print("Imported Bucklespring original WAV recordings:",
          import_bucklespring(args.archive, args.destination))


if __name__ == "__main__":
    main()
