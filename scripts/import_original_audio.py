"""Merge original WAV-only navSounds packs and a full ScreenReaderSounds add-on.

Only PCM WAV bytes are copied. No sound is synthesized or converted, and no
Python/DLL from external add-ons is executed or installed. When two sources
assign the same event in Voiceover, ScreenReaderSounds has priority.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins" / "soundThemes"))
from catalog import LEGACY_EVENTS, TYPING_EVENTS, canonical_name  # noqa: E402

ASSETS = ROOT / "globalPlugins" / "soundThemes" / "effects"
EVENT_RE = re.compile(r"^[a-z]+\.[a-z0-9_]+$")
MAX_FILE_SIZE = 8 * 1024 * 1024
MAX_TOTAL_SIZE = 120 * 1024 * 1024
MAX_FILES = 3000

# The user's complete ScreenReaderSounds theme is distributed as a flat ZIP
# with nested objdata.zip; these entries are NOT under globalPlugins/voiceover.
SRS_SPECIAL = {
    "clicked": "nav.activate", "longclicked": "nav.long_activate",
    "closed": "nav.close", "opened": "nav.open",
    "collapsed": "nav.collapse", "expanded": "nav.expand",
    "complete": "system.complete", "eclose": "nav.edit_exit",
    "end": "key.home_end", "error": "key.invalid",
    "italic": "state.italic", "notext": "nav.empty",
    "media": "system.media", "pausedfeedback": "system.paused_feedback",
    "scroll": "nav.scroll", "shifttab": "key.shift_tab",
    "tutorialtrigger": "system.tutorial", "typekey": "key.character",
    "typekeypr": "key.protected", "typekeyremove": "key.backspace",
    "typekeyspace": "key.space", "unlockscreen": "system.unlock",
    "lock": "system.lock", "lockscreen": "system.lockscreen",
}
SRS_OGG = {"ready": "system.ready", "tick": "nav.tick",
           "volumebeep": "system.volume_beep"}
SRS_KEYBOARD = {"shifttab": "keyboard.shift_tab", "end": "keyboard.end",
                "typekeyremove": "keyboard.backspace"}


def checked_wav(contents: bytes, label: str) -> None:
    if not contents or len(contents) > MAX_FILE_SIZE:
        raise ValueError(f"Missing or oversized WAV: {label}")
    try:
        with wave.open(io.BytesIO(contents), "rb") as file:
            if (file.getcomptype() != "NONE" or file.getnchannels() not in (1, 2)
                    or file.getsampwidth() not in (1, 2, 3, 4)
                    or file.getframerate() < 8000
                    or file.getnframes() / file.getframerate() > 30):
                raise ValueError(f"Unsupported PCM WAV: {label}")
    except (wave.Error, EOFError) as error:
        raise ValueError(f"Invalid WAV: {label}") from error


def wav_members(archive_path: Path):
    """Yield (original path, basename, file bytes) without extracting paths."""
    with ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_TOTAL_SIZE:
            raise ValueError(f"Oversized archive: {archive_path}")
        if archive.testzip() is not None:
            raise ValueError(f"Corrupt archive: {archive_path}")
        for member in members:
            if member.is_dir() or Path(member.filename).suffix.lower() != ".wav":
                continue
            if member.file_size > MAX_FILE_SIZE:
                raise ValueError(f"Oversized WAV: {member.filename}")
            contents = archive.read(member)
            checked_wav(contents, member.filename)
            yield member.filename.replace("\\", "/"), Path(member.filename).stem, contents


def save_event(destination: Path, kind: str, pack: str, event: str,
               data: bytes, *, replace: bool = False) -> bool:
    if (kind not in ("navigation", "typing", "keyboard") or pack not in
            ("voiceover", "classic-typewriter", "talkback-5", "talkback-6")
            or not EVENT_RE.fullmatch(event)
            or ((kind == "keyboard") != event.startswith("keyboard."))
            or (kind != "keyboard" and (event in TYPING_EVENTS) != (kind == "typing"))):
        raise ValueError(f"Invalid audio destination: {kind}/{pack}/{event}")
    folder = destination / kind / pack
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (event + ".wav")
    if target.exists() and (not replace or target.read_bytes() == data):
        return False
    target.write_bytes(data)
    return True


def add_navsounds_navigation(archive: Path, destination: Path) -> dict:
    """navSounds' lowercase tab.wav is role.tab, NOT the Tab keystroke."""
    events = set()
    count = 0
    for path, stem, contents in wav_members(archive):
        if "/" in path or "\\" in path:
            raise ValueError("Expected a single flat navSounds navigation pack")
        event = "role." + canonical_name(stem)
        if not EVENT_RE.fullmatch(event):
            raise ValueError(f"Invalid navSounds role filename: {path}")
        if event in events:
            continue
        events.add(event)
        count += int(save_event(destination, "navigation", "voiceover", event, contents))
    if not events:
        raise ValueError("navSounds navigation ZIP has no WAV files")
    return {"source": str(archive), "pack": "navigation/voiceover", "events": len(events), "written": count}


def add_navsounds_typing(archive: Path, destination: Path) -> dict:
    """Every file in Classic Typewriter is a variation in THIS typing pack."""
    events = set()
    count = 0
    for path, stem, contents in wav_members(archive):
        if "/" in path or "\\" in path:
            raise ValueError("Expected a single flat navSounds typing pack")
        event = "key.character" + (f"__{canonical_name(stem)}" if stem else "")
        if not re.fullmatch(r"key\.character__[a-z0-9_]+", event):
            raise ValueError(f"Invalid typing sound filename: {path}")
        if event in events:
            continue
        events.add(event)
        folder = destination / "typing" / "classic-typewriter"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (event + ".wav")
        if not target.exists():
            target.write_bytes(contents)
            count += 1
    if not events:
        raise ValueError("navSounds typing ZIP has no WAV files")
    return {"source": str(archive), "pack": "typing/classic-typewriter", "variations": len(events), "written": count}


def screenreader_location(path: str) -> tuple[str, bool] | None:
    """Recognize the three original ScreenReaderSounds theme roots."""
    chunks = [p.lower() for p in path.split("/") if p]
    if "voiceover" not in chunks:
        return None
    tail = chunks[chunks.index("voiceover") + 1:]
    pack = "voiceover"
    if len(tail) >= 3 and tail[:2] in (["talkback", "one"], ["talkback", "two"]):
        pack = "talkback-5" if tail[1] == "one" else "talkback-6"
        tail = tail[2:]
    if len(tail) == 2 and tail[0] == "objdata" and tail[1].endswith(".wav"):
        return pack, True
    if len(tail) == 1 and tail[0].endswith(".wav"):
        return pack, False
    return None


def add_screenreader_sounds(archive: Path, destination: Path) -> dict:
    """ScreenReaderSounds WAV overrides navSounds for the SAME canonical event."""
    entries = []
    for path, stem, contents in wav_members(archive):
        where = screenreader_location(path)
        if where:
            pack, is_role = where
            event = "role." + canonical_name(stem) if is_role else LEGACY_EVENTS.get(canonical_name(stem))
            if event:
                kind = "typing" if event in TYPING_EVENTS else "navigation"
                # Two old SRS filenames may point to one canonical event.
                rank = 0 if canonical_name(stem) == "typekeyremove" else 1
                entries.append((rank, kind, pack, event, contents))
        elif path.lower().startswith("screenreadersounds/") and path.count("/") == 1:
            name = canonical_name(stem)
            if name in SRS_SPECIAL:
                event = SRS_SPECIAL[name]
            elif name in ("edetabletext", "hedingh"):
                event = "role.editabletext" if name == "edetabletext" else "role.heading"
            else:
                event = "role." + name
            kind = "typing" if event in TYPING_EVENTS else "navigation"
            entries.append((3, kind, "voiceover", event, contents))
            if name in SRS_KEYBOARD:
                entries.append((2, "keyboard", "voiceover", SRS_KEYBOARD[name], contents))
    # The full ZIP also contains a distinct objdata.zip with non-duplicate
    # recordings for its roles. Prefer those genuine sounds over top-level
    # placeholders which often repeat exactly the same recording.
    with ZipFile(archive) as source:
        nested_name = next((n for n in source.namelist()
                            if n.lower().endswith("/objdata.zip")), None)
        if nested_name:
            contents = source.read(nested_name)
            with ZipFile(io.BytesIO(contents)) as nested:
                for member in nested.infolist():
                    if member.is_dir() or not member.filename.lower().endswith(".wav"):
                        continue
                    if member.file_size > MAX_FILE_SIZE:
                        raise ValueError(f"Oversized nested sound: {member.filename}")
                    data = nested.read(member)
                    checked_wav(data, member.filename)
                    stem = Path(member.filename).stem
                    event = "role." + canonical_name(stem)
                    entries.append((1, "navigation", "voiceover", event, data))
        # Optional OGG recordings are decoded offline from the original audio
        # bytes, never synthesized; end users still get individual PCM WAVs.
        for member in source.infolist():
            if not member.filename.lower().startswith("screenreadersounds/"):
                continue
            if member.filename.count("/") != 1 or not member.filename.lower().endswith(".ogg"):
                continue
            event = SRS_OGG.get(canonical_name(Path(member.filename).stem))
            if event:
                data = decode_original_ogg(source.read(member))
                entries.append((2, "navigation", "voiceover", event, data))
    entries.sort(key=lambda entry: entry[0])
    if not entries:
        raise ValueError("No original ScreenReaderSounds WAVs were found in this archive")
    seen = set()
    updated = 0
    for _, kind, pack, event, contents in entries:
        if (kind, pack, event) in seen:
            continue
        seen.add((kind, pack, event))
        updated += int(save_event(destination, kind, pack, event, contents, replace=True))
    return {"source": str(archive), "distinct_events": len(seen), "written": updated,
            "packs": sorted({f"{kind}/{pack}" for kind, pack, _ in seen})}


def decode_original_ogg(contents: bytes) -> bytes:
    """Preserve original OGG audio by decoding it to PCM WAV with ffmpeg."""
    if not contents or len(contents) > MAX_FILE_SIZE:
        raise ValueError("Invalid OGG asset")
    with tempfile.TemporaryDirectory(prefix="nvda-original-audio-") as temp:
        source = Path(temp) / "original.ogg"
        output = Path(temp) / "original.wav"
        source.write_bytes(contents)
        try:
            result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                                     "-i", str(source), "-acodec", "pcm_s16le", str(output)],
                                    capture_output=True, timeout=25, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError("ffmpeg is required to preserve original OGG recordings") from error
        if result.returncode:
            raise ValueError("ffmpeg could not decode an original OGG sound")
        result_bytes = output.read_bytes()
        checked_wav(result_bytes, "converted original OGG")
        return result_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nav-voiceover", type=Path)
    parser.add_argument("--nav-typing", type=Path)
    parser.add_argument("--screenreader-addon", type=Path)
    parser.add_argument("--destination", type=Path, default=ASSETS)
    args = parser.parse_args()
    if not (args.nav_voiceover or args.nav_typing or args.screenreader_addon):
        parser.error("Specify at least one original audio ZIP or full add-on")
    for filename, fn in ((args.nav_voiceover, add_navsounds_navigation),
                         (args.nav_typing, add_navsounds_typing),
                         (args.screenreader_addon, add_screenreader_sounds)):
        if filename:
            print(fn(filename, args.destination))


if __name__ == "__main__":
    main()
