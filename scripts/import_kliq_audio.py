"""Import genuine individual Kliq key-down WAVs without bundling unused up WAVs.

Usage: python soundThemes/scripts/import_kliq_audio.py upload/Sounds.zip

Kliq is Copyright (c) 2026 Crafter Station, MIT licensed. Its keyboard
recordings were supplied by the user as Sounds.zip. Audio is never generated.
"""

from __future__ import annotations

import argparse
import io
import re
import wave
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EFFECTS = ROOT / "globalPlugins" / "soundThemes" / "effects"
SETS = ("Cherry", "DSA", "KAT", "MT3", "OEM", "SA", "XDA")
MAX_AUDIO_BYTES = 8 * 1024 * 1024
MEMBER = re.compile(r"^Sounds/(Cherry|DSA|KAT|MT3|OEM|SA|XDA)/([0-9]+)-down\.wav$")

# IBM PC set-1 scan codes, plus the extended codes used by the Kliq source.
SCAN_EVENTS = {
    1: "escape", 12: "minus", 13: "equals", 14: "backspace",
    15: "tab", 26: "left_bracket", 27: "right_bracket", 28: "enter",
    29: "left_ctrl", 39: "semicolon", 40: "apostrophe",
    41: "backtick", 42: "left_shift", 43: "backslash",
    51: "comma", 52: "period", 53: "slash", 54: "right_shift",
    55: "multiply", 56: "left_alt", 57: "space", 58: "capslock",
    3640: "right_alt", 3675: "left_windows", 3676: "right_windows",
    57416: "up", 57419: "left", 57421: "right", 57424: "down",
}
for first, letters in ((16, "qwertyuiop"), (30, "asdfghjkl"), (44, "zxcvbnm")):
    SCAN_EVENTS.update({first + offset: name for offset, name in enumerate(letters)})
SCAN_EVENTS.update({2 + i: str((i + 1) % 10) for i in range(10)})
SCAN_EVENTS.update({59 + i: f"f{i + 1}" for i in range(10)})
SCAN_EVENTS.update({87: "f11", 88: "f12"})


def _validate(contents: bytes, name: str):
    if not contents or len(contents) > MAX_AUDIO_BYTES:
        raise ValueError(f"Invalid WAV size: {name}")
    try:
        with wave.open(io.BytesIO(contents)) as wav:
            if (wav.getcomptype() != "NONE" or wav.getnchannels() not in (1, 2)
                    or wav.getsampwidth() not in (1, 2, 3, 4)
                    or wav.getframerate() < 8000
                    or wav.getnframes() / wav.getframerate() > 30):
                raise ValueError(f"Unsupported PCM WAV: {name}")
    except (EOFError, wave.Error) as error:
        raise ValueError(f"Invalid PCM WAV: {name}") from error


def import_kliq(archive_path: Path, destination: Path = EFFECTS) -> dict[str, int]:
    """Import only actual key-down samples into the seven distinct packs."""
    archive_path = Path(archive_path)
    extracted = {name: {} for name in SETS}
    with ZipFile(archive_path) as archive:
        if len(archive.infolist()) > 1500 or sum(m.file_size for m in archive.infolist()) > 150_000_000:
            raise ValueError("Unexpectedly large Kliq archive")
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Damaged archive at {bad}")
        for info in archive.infolist():
            match = MEMBER.fullmatch(info.filename)
            if not match:
                continue
            set_name, code = match.group(1), int(match.group(2))
            event = SCAN_EVENTS.get(code)
            if event is None:
                continue
            data = archive.read(info)
            _validate(data, info.filename)
            extracted[set_name].setdefault("keyboard." + event, data)
        # The original single mouse-click recording can also serve a hover
        # event in navigation mode without introducing any synthetic audio.
        mouse_data = None
        if "Sounds/click.wav" in archive.namelist():
            mouse_data = archive.read("Sounds/click.wav")
            _validate(mouse_data, "Sounds/click.wav")

    if any(not sound_map for sound_map in extracted.values()):
        raise ValueError("The seven Kliq recording sets must all be present")

    report = {}
    for set_name, sound_map in extracted.items():
        folder = Path(destination) / "keyboard" / set_name.lower()
        folder.mkdir(parents=True, exist_ok=True)
        # F-keys, numpad, media and unusual hardware keys have no dedicated
        # recording in many sets. The real space-bar sound from the SAME set
        # is a fixed, non-random fallback; it does not create 200 duplicates.
        fallback = sound_map.get("keyboard.space") or next(iter(sound_map.values()))
        sound_map["keyboard.default"] = fallback
        for event, data in sound_map.items():
            (folder / f"{event}.wav").write_bytes(data)
        report[set_name.lower()] = len(sound_map)
    if mouse_data is not None:
        mouse_target = Path(destination) / "navigation" / "voiceover" / "nav.mouse.wav"
        mouse_target.parent.mkdir(parents=True, exist_ok=True)
        if not mouse_target.exists():
            mouse_target.write_bytes(mouse_data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--destination", type=Path, default=EFFECTS)
    args = parser.parse_args()
    print("Imported genuine Kliq key-down WAV events:", import_kliq(args.archive, args.destination))


if __name__ == "__main__":
    main()
