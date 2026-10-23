"""Import the user's original navSounds/default and typing packs from effects.zip.

The audio is copied byte-for-byte from the supplied archive. Identical samples
within one event/pack are stored once. The source-specific spelling fixes are
important: merely copying ``expended.wav`` and ``tableraw.wav`` into an NVDA
theme leaves them unreachable by real State/Role callbacks.

Run: python scripts/import_effects_archive.py ../upload/effects.zip
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import wave
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION = ROOT / "globalPlugins" / "soundThemes" / "effects"
NAV_PREFIX = "effects/navsounds/default/"
TYPING_PREFIX = "effects/typingsound/"

# These source filenames are not literal names of current NVDA control roles.
# Prefer a real controlTypes.Role / State or a supported canonical event.
NAV_SPECIAL = {
    "activity": "role.busyindicator",  # current NVDA Role.BUSY_INDICATOR
    "caret": "nav.caret",
    "clickable": "state.clickable",
    "complete": "system.complete",
    "empty": "nav.empty",
    "item": "nav.selection",  # generic legacy item, not an NVDA Role.ITEM
    "expended": "state.expanded",
    "invisibled": "state.invisible",
    "tablecoulmnheader": "role.tablecolumnheader",
    "tableraw": "role.tablerow",
    "checked": "state.checked",
    "halfchecked": "state.halfchecked",
    "halfpressed": "state.halfpressed",
    "invalidentry": "state.invalidentry",
    "offscreen": "state.offscreen",
    "on": "state.on",
    "off": "state.off",  # negative transition of State.ON
    "pressed": "state.pressed",
    "protected": "state.protected",
    "required": "state.required",
    "unavailable": "state.unavailable",
    "visited": "state.visited",
    # Several upstream filenames describe the same editable control. Prefer
    # the well-named editabletext.wav, but never lose unrelated role WAVs.
    "edittext": "role.editabletext",
}

# Repair exact destinations created by an older run of this same importer.
# Only remove an old alias if the bytes equal the uploaded original and the
# correctly named replacement exists. Never delete third-party user audio.
PREVIOUS_ALIASES = {
    "activity": "role.activityindicator",
    "item": "role.item",
    "on": "role.on",
    "off": "role.off",
}

TYPING_FOLDERS = {
    "1blueswitch": "blue-switch",
    "2redswitch": "red-switch",
    "3brownswitche": "brown-switch",
    "androidkeyboard1": "android-keyboard-1",
    "androidkeyboard2": "android-keyboard-2",
    "classic typewriter": "classic-typewriter",
    "iphonekeyboard": "iphone-keyboard",
    "key1": "key-1",
    "key2": "key-2",
    "perkins braill": "perkins-braille",
    "samsung1": "samsung-1",
    "samsung2": "samsung-2",
}

_STEM = re.compile(r"[^a-z0-9]")
_EVENT = re.compile(r"^[a-z]+\.[a-z0-9_]+$")


def navigation_event(stem: str) -> str:
    canonical = _STEM.sub("", stem.lower())
    event = NAV_SPECIAL.get(canonical, "role." + canonical)
    if not _EVENT.fullmatch(event):
        raise ValueError(f"Invalid navigation event: {stem}")
    return event


def typing_event(stem: str) -> str:
    canonical = _STEM.sub("", stem.lower())
    if canonical in ("delete", "backspace"):
        return "key.backspace"
    if canonical in ("space", "spacebar", "keypressspaceba1646393970802"):
        return "key.space"
    if canonical == "bill":
        return "key.enter"  # classic typewriter carriage bell
    return "key.character"


def check_wav(data: bytes, name: str) -> None:
    if not data or len(data) > 8 * 1024 * 1024:
        raise ValueError(f"Missing or oversized WAV: {name}")
    try:
        with wave.open(io.BytesIO(data), "rb") as sound:
            if (sound.getcomptype() != "NONE" or sound.getnchannels() not in (1, 2)
                    or sound.getsampwidth() not in (1, 2, 3, 4)
                    or sound.getframerate() < 8000
                    or sound.getnframes() / sound.getframerate() > 30):
                raise ValueError(f"Unsupported PCM WAV: {name}")
    except (wave.Error, EOFError) as error:
        raise ValueError(f"Invalid WAV: {name}") from error


def import_archive(source: Path, destination: Path = DEFAULT_DESTINATION) -> dict:
    """Add 86 navigation and 61 typing source samples without touching other packs.

    Always preserve the SRS-priority samples already in voiceover. Only
    missing voiceover events are filled from the supplied default pack, so
    people using the old selected theme also hear newly covered NVDA roles.
    """
    incoming = defaultdict(list)
    source_counts = defaultdict(int)
    with ZipFile(source) as archive:
        members = archive.infolist()
        if len(members) > 400 or sum(member.file_size for member in members) > 32 * 1024 * 1024:
            raise ValueError("effects.zip is unexpectedly large")
        if archive.testzip() is not None:
            raise ValueError("effects.zip is damaged")
        for member in members:
            if member.is_dir() or not member.filename.lower().endswith(".wav"):
                continue
            filename = member.filename.replace("\\", "/")
            components = filename.split("/")
            if (".." in components or len(components) != 4
                    or not filename.startswith("effects/")):
                raise ValueError(f"Unexpected WAV location: {filename}")
            if filename.startswith(NAV_PREFIX):
                kind, pack = "navigation", "default"
                event = navigation_event(Path(filename).stem)
            elif filename.startswith(TYPING_PREFIX):
                kind = "typing"
                pack = TYPING_FOLDERS.get(components[2].lower())
                if pack is None:
                    raise ValueError(f"Unexpected typing pack: {components[2]}")
                event = typing_event(Path(filename).stem)
            else:
                raise ValueError(f"Unexpected sound folder: {filename}")
            data = archive.read(member)
            check_wav(data, filename)
            incoming[(kind, pack, event)].append((Path(filename).stem.lower(), data))
            source_counts[kind] += 1

    if dict(source_counts) != {"navigation": 86, "typing": 61}:
        raise ValueError(f"Unexpected original sound counts: {dict(source_counts)}")

    written = 0
    merged_voiceover = 0
    for (kind, pack, event), samples in sorted(incoming.items()):
        folder = destination / kind / pack
        folder.mkdir(parents=True, exist_ok=True)
        # Explicit, correctly spelled filename wins if upstream contains
        # multiple aliases for the same NVDA role.
        samples.sort(key=lambda entry: (entry[0] != event.split(".", 1)[1], entry[0]))
        hashes = set()
        for existing in folder.glob(f"{event}*.wav"):
            if existing.stem == event or existing.stem.startswith(event + "__"):
                hashes.add(hashlib.sha256(existing.read_bytes()).hexdigest())
        for _, data in samples:
            digest = hashlib.sha256(data).hexdigest()
            if digest in hashes or (kind == "navigation" and hashes):
                continue
            filename = event + (f"__{digest[:12]}" if hashes else "") + ".wav"
            target = folder / filename
            if target.exists() and target.read_bytes() != data:
                raise ValueError(f"Conflicting WAV: {target}")
            if not target.exists():
                target.write_bytes(data)
                written += 1
            hashes.add(digest)
        if kind == "navigation":
            source_file = folder / (event + ".wav")
            voiceover_file = destination / "navigation" / "voiceover" / (event + ".wav")
            if source_file.is_file() and not voiceover_file.exists():
                voiceover_file.parent.mkdir(parents=True, exist_ok=True)
                voiceover_file.write_bytes(source_file.read_bytes())
                merged_voiceover += 1
    for stem, obsolete_event in PREVIOUS_ALIASES.items():
        correct_event = navigation_event(stem)
        original_samples = incoming[("navigation", "default", correct_event)]
        original_bytes = next((data for original_name, data in original_samples
                               if original_name == stem), None)
        if original_bytes is None:
            continue
        for pack in ("default", "voiceover"):
            folder = destination / "navigation" / pack
            obsolete = folder / (obsolete_event + ".wav")
            replacement = folder / (correct_event + ".wav")
            if (obsolete.is_file() and replacement.is_file()
                    and obsolete.read_bytes() == original_bytes):
                obsolete.unlink()
    return {"source_counts": dict(source_counts), "written": written,
            "voiceover_gaps_filled": merged_voiceover,
            "typing_packs": sorted(TYPING_FOLDERS.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    print(import_archive(args.archive, args.destination))


if __name__ == "__main__":
    main()
