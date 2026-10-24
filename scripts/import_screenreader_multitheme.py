"""Import a ScreenReaderSounds archive with separate TalkBack/VoiceOver packs.

The user's archive contains ScreenReaderSounds/{talkback,voiceover} with native
role WAV names such as checkbox.wav, and a nested VoiceOver objdata.zip.
Canonical event assignments play correctly in NVDA and keep their familiar,
prefix-free names in the editor. ScreenReaderSounds WAVs replace earlier
navSounds files for duplicate canonical events, never a random variation.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from zipfile import ZipFile

from import_original_audio import (
    ASSETS, LEGACY_EVENTS, SRS_OGG, SRS_SPECIAL, TYPING_EVENTS,
    checked_wav, decode_original_ogg, save_event, wav_members,
)
from catalog import canonical_name


def import_multitheme(source: Path, destination: Path = ASSETS) -> dict:
    source = Path(source)
    choices = {}  # (kind, pack, event) -> (priority, genuine PCM bytes)

    def offer(pack: str, filename: str, data: bytes, priority: int):
        normalized = canonical_name(Path(filename).stem)
        event = SRS_SPECIAL.get(normalized) or LEGACY_EVENTS.get(normalized)
        if event is None:
            # Plain names are NVDA roles: checkbox, textbox, heading, etc.
            event = "role." + normalized
        kind = "typing" if event in TYPING_EVENTS else "navigation"
        key = (kind, pack, event)
        earlier = choices.get(key)
        if earlier is None or priority < earlier[0]:
            choices[key] = (priority, data)

    for original, stem, data in wav_members(source):
        parts = original.replace("\\", "/").split("/")
        if (len(parts) != 3 or parts[0].lower() != "screenreadersounds"
                or parts[1].lower() not in ("talkback", "voiceover")):
            continue
        priority = 0 if canonical_name(stem) == "typekeyremove" else 2
        offer(parts[1].lower(), parts[2], data, priority)

    with ZipFile(source) as archive:
        for name in archive.namelist():
            parts = name.replace("\\", "/").split("/")
            if len(parts) != 3 or parts[0].lower() != "screenreadersounds":
                continue
            pack, filename = parts[1].lower(), parts[2]
            if pack == "voiceover" and filename.lower() == "objdata.zip":
                with ZipFile(io.BytesIO(archive.read(name))) as nested:
                    if nested.testzip() is not None or len(nested.infolist()) > 500:
                        raise ValueError("Damaged or oversized nested role archive")
                    for member in nested.infolist():
                        if member.is_dir() or Path(member.filename).suffix.lower() != ".wav":
                            continue
                        audio = nested.read(member)
                        checked_wav(audio, member.filename)
                        # The inner directory contains role-specific takes.
                        offer("voiceover", Path(member.filename).name, audio, 1)
            elif pack in ("talkback", "voiceover") and filename.lower().endswith(".ogg"):
                normalized = canonical_name(Path(filename).stem)
                if normalized in SRS_OGG:
                    offer(pack, filename, decode_original_ogg(archive.read(name)), 2)

    if not any(pack == "voiceover" for _, pack, _ in choices):
        raise ValueError("Missing VoiceOver source audio")
    if not any(pack == "talkback" for _, pack, _ in choices):
        raise ValueError("Missing TalkBack source audio")

    written = 0
    overwritten = 0
    counts = {}
    for (kind, pack, event), (_, data) in sorted(choices.items()):
        existing = destination / kind / pack / (event + ".wav")
        if existing.is_file() and existing.read_bytes() != data:
            overwritten += 1
        written += int(save_event(destination, kind, pack, event, data, replace=True))
        counts[f"{kind}/{pack}"] = counts.get(f"{kind}/{pack}", 0) + 1
    return {"mapped": counts, "written": written, "screenreader_preferred_on_conflict": overwritten}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", type=Path, default=ASSETS)
    args = parser.parse_args()
    print(import_multitheme(args.source, args.destination))


if __name__ == "__main__":
    main()
