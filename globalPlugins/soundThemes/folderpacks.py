"""Manifest-free WAV sound packs, following navSounds' directory convention.

Each folder is one sound theme; filenames identify events without theme.json.
An ordinary unknown filename in a typing pack denotes a randomized key sound.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import uuid
import wave
from pathlib import Path, PureWindowsPath
from zipfile import ZipFile, ZIP_DEFLATED

from .catalog import canonical_name, candidates, is_keyboard_event, is_typing_event, legacy_event_for_filename
from .keyboard_catalog import all_keyboard_events

_KEYBOARD_NAMES = {event for _, event, _ in all_keyboard_events()}
_KEYBOARD_ALIASES = {event.split(".", 1)[1]: event for event in _KEYBOARD_NAMES}
_KEYBOARD_ALIASES.update({
    **{f"key{chr(97 + n)}": f"keyboard.{chr(97 + n)}" for n in range(26)},
    **{f"digit{n}": f"keyboard.{n}" for n in range(10)},
    "esc": "keyboard.escape", "return": "keyboard.enter",
    "spacebar": "keyboard.space", "controlleft": "keyboard.left_ctrl",
    "controlright": "keyboard.right_ctrl", "shiftleft": "keyboard.left_shift",
    "shiftright": "keyboard.right_shift", "altleft": "keyboard.left_alt",
    "altright": "keyboard.right_alt", "metaleft": "keyboard.left_windows",
    "metaright": "keyboard.right_windows", "arrowup": "keyboard.up",
    "arrowdown": "keyboard.down", "arrowleft": "keyboard.left",
    "arrowright": "keyboard.right", "pageup": "keyboard.pageup",
    "pagedown": "keyboard.pagedown", "brightnessdown": "keyboard.brightness_down",
    "brightnessup": "keyboard.brightness_up", "mediaplaypause": "keyboard.media_play_pause",
})

MAX_WAV_SIZE = 8 * 1024 * 1024
MAX_ZIP_SIZE = 80 * 1024 * 1024
MAX_FILES = 800
EVENT_PATTERN = re.compile(r"^(?:[a-z]+\.)?[a-z0-9_]+$")
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                     *(f"lpt{i}" for i in range(1, 10))}
_COMMON_STATES = {"expanded", "collapsed", "checked", "unchecked", "selected",
                  "pressed", "readonly", "protected", "focused", "required", "busy",
                  "invalidentry", "multiline", "editable", "disabled", "invisible"}


def safe_slug(name: str) -> str:
    """Keep meaningful Thai/Unicode names but disallow Windows path escapes."""
    name = name.strip()
    if not name or name in (".", "..") or len(name) > 80 or _FORBIDDEN.search(name):
        raise ValueError("Invalid sound pack name (no separators, controls or Windows special symbols)")
    slug = re.sub(r"\s+", "-", name).strip(" .")
    if not slug or slug.lower().split(".")[0] in _WINDOWS_RESERVED or slug.endswith("."):
        raise ValueError("This sound pack name is reserved on Windows")
    return slug.lower() if slug.isascii() else slug


def validate_wave(path: Path):
    if not path.is_file() or path.stat().st_size > MAX_WAV_SIZE:
        raise ValueError("The WAV file does not exist or exceeds 8 MB")
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getcomptype() != "NONE" or wav.getsampwidth() not in (1, 2, 3, 4):
                raise ValueError("Please use uncompressed PCM WAV files")
            if wav.getnchannels() not in (1, 2) or wav.getframerate() < 8000:
                raise ValueError("Please use mono or stereo WAV at 8 kHz or higher")
            if wav.getnframes() / wav.getframerate() > 30:
                raise ValueError("Sound must be no longer than 30 seconds")
    except (wave.Error, EOFError) as error:
        raise ValueError("Invalid PCM WAV file") from error


def _runtime_roles_states():
    try:
        from controlTypes import Role, State
        return Role, State
    except ImportError:
        return (), ()


def event_for_filename(stem: str, kind: str, roles=(), states=()) -> str | None:
    """Canonical event.wav, event__variant.wav, or old unprefixed WAV name."""
    base = stem.split("__", 1)[0].lower()
    if kind == "keyboard":
        normalized = canonical_name(base)
        event = (base if base.startswith("keyboard.")
                 else _KEYBOARD_ALIASES.get(base) or _KEYBOARD_ALIASES.get(normalized))
        return event if event in _KEYBOARD_NAMES else None
    # navSounds' lowercase tab.wav denotes the Role.TAB control, whereas
    # ScreenReaderSounds' capitalized Tab.wav denotes the Tab keystroke.
    # Preserve the original filename case before applying legacy aliases.
    if kind == "navigation" and stem.split("__", 1)[0] == "tab":
        return "role.tab"
    if EVENT_PATTERN.fullmatch(base) and "." in base:
        event = base
    else:
        event = legacy_event_for_filename(base, roles, states)
        if event is None:
            normalized = canonical_name(base)
            if kind == "typing":
                return "key.character"
            if not normalized:
                return None
            event = "state." + normalized if normalized in _COMMON_STATES else "role." + normalized
    if kind == "typing" and not is_typing_event(event):
        return None
    if kind == "navigation" and (is_typing_event(event) or is_keyboard_event(event)):
        return None
    return event


class ThemeStore:
    def __init__(self, packaged: Path, writable: Path, kind: str = "mixed"):
        if kind not in ("navigation", "typing", "keyboard", "mixed"):
            raise ValueError("Invalid sound pack category")
        self.packaged = Path(packaged)
        self.writable = Path(writable)
        self.kind = kind

    def accepts(self, event: str) -> bool:
        if self.kind == "mixed":
            return True
        if self.kind == "keyboard":
            return event in _KEYBOARD_NAMES
        if is_keyboard_event(event):
            return False
        return is_typing_event(event) == (self.kind == "typing")

    def themes(self) -> list[tuple[str, str]]:
        result = []
        for prefix, base in (("builtin", self.packaged), ("user", self.writable)):
            if not base.is_dir():
                continue
            for folder in sorted(base.iterdir(), key=lambda p: p.name.casefold()):
                if folder.is_dir() and not folder.name.startswith("."):
                    result.append((f"{prefix}:{folder.name}", folder.name.replace("-", " ").title()))
        return result

    def directory(self, theme_id: str) -> Path:
        if ":" not in theme_id:
            raise ValueError("Invalid sound pack identifier")
        source, slug = theme_id.split(":", 1)
        if source not in ("builtin", "user") or safe_slug(slug) != slug:
            raise ValueError("Invalid sound pack identifier")
        return (self.packaged if source == "builtin" else self.writable) / slug

    def _read_sound_map(self, folder: Path) -> dict[str, list[str]]:
        if not folder.is_dir():
            raise FileNotFoundError("Sound pack does not exist")
        role_names, state_names = _runtime_roles_states()
        mapping = {}
        for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
            if not path.is_file() or path.suffix.lower() != ".wav":
                continue
            event = event_for_filename(path.stem, self.kind, role_names, state_names)
            if event and self.accepts(event):
                mapping.setdefault(event, []).append(path.name)
        return mapping

    def load(self, theme_id: str) -> dict:
        folder = self.directory(theme_id)
        mapping = self._read_sound_map(folder)
        return {"name": folder.name.replace("-", " ").title(), "kind": self.kind,
                "sounds": {event: value if len(value) > 1 else value[0]
                           for event, value in mapping.items()}}

    def sound_for(self, theme_id: str, event: str) -> Path | None:
        try:
            folder = self.directory(theme_id)
            mapping = self.load(theme_id)["sounds"]
            for key in candidates(event):
                values = mapping.get(key)
                if values:
                    ordered = values if isinstance(values, list) else [values]
                    if self.kind != "keyboard":
                        ordered = random.sample(ordered, len(ordered))
                    for name in ordered:
                        path = folder / name
                        if path.is_file():
                            return path
        except (OSError, ValueError, KeyError):
            pass
        return None

    def preview_sound(self, theme_id: str) -> Path | None:
        """Pick one REAL recording from this pack for instant list navigation.

        Deliberately avoid role/keyboard fallbacks, randomness and other packs.
        The common representative cue comes first; sparse custom packs use
        their first valid file instead of remaining silent unnecessarily.
        """
        priorities = {
            "navigation": ("role.listitem", "role.treeviewitem", "role.button", "nav.focus"),
            "typing": ("key.character", "key.space", "key.backspace"),
            "keyboard": ("keyboard.a", "keyboard.space", "keyboard.default"),
        }.get(self.kind, ())
        try:
            folder = self.directory(theme_id)
            mapped = self.load(theme_id)["sounds"]
            for event in (*priorities, *sorted(mapped)):
                filenames = mapped.get(event)
                if not filenames:
                    continue
                for filename in (filenames if isinstance(filenames, list) else [filenames]):
                    candidate = folder / filename
                    if candidate.is_file():
                        return candidate
        except (OSError, ValueError, KeyError):
            pass
        return None

    def create(self, name: str, base: str | None = None) -> str:
        identifier = "user:" + safe_slug(name)
        destination = self.directory(identifier)
        if destination.exists():
            raise FileExistsError("A sound pack with that name already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if base:
            source = self.directory(base)
            self.load(base)
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns("theme.json"))
        else:
            destination.mkdir(parents=True)
        return identifier

    def rename(self, theme_id: str, new_name: str) -> str:
        if not theme_id.startswith("user:"):
            raise PermissionError("Built-in sound packs are read-only")
        destination_id = "user:" + safe_slug(new_name)
        old = self.directory(theme_id)
        destination = self.directory(destination_id)
        if destination != old:
            if destination.exists():
                raise FileExistsError("A sound pack with that name already exists")
            old.rename(destination)
        return destination_id

    def delete(self, theme_id: str):
        if not theme_id.startswith("user:"):
            raise PermissionError("Built-in sound packs cannot be deleted")
        self.load(theme_id)
        shutil.rmtree(self.directory(theme_id))

    def _unused(self, folder: Path, name: str):
        target = folder / "_unused"
        target.mkdir(exist_ok=True)
        (folder / name).replace(target / (uuid.uuid4().hex[:8] + "-" + name))

    def assign(self, theme_id: str, event: str, file: Path | None, append: bool = False):
        if not theme_id.startswith("user:"):
            raise PermissionError("Built-in sound packs are read-only")
        if not EVENT_PATTERN.fullmatch(event) or not self.accepts(event):
            raise ValueError("Invalid event or event belongs to another sound pack type")
        if self.kind == "keyboard" and append:
            raise ValueError("Keyboard sounds use exactly one WAV for each named key")
        folder = self.directory(theme_id)
        if file is not None:
            file = Path(file)
            validate_wave(file)
        if not append or file is None:
            for existing in self._read_sound_map(folder).get(event, []):
                self._unused(folder, existing)
        if file is not None:
            filename = (f"{event}__{uuid.uuid4().hex[:8]}.wav" if append
                        else f"{event}.wav")
            shutil.copyfile(file, folder / filename)

    @staticmethod
    def _safe_zip_name(name: str) -> bool:
        value = PureWindowsPath(name)
        return (not value.drive and not value.is_absolute() and ":" not in name
                and "\\" not in name and name not in ("", ".")
                and not name.startswith("/") and ".." not in Path(name).parts)

    def _import_files(self, files: list[tuple[Path, str]], name: str, roles=(), states=()) -> str:
        identifier = self.create(name)
        folder = self.directory(identifier)
        groups = {}
        try:
            for path, stem in files:
                event = event_for_filename(stem, self.kind, roles, states)
                if event is None or not self.accepts(event):
                    continue
                try:
                    validate_wave(path)
                except ValueError:
                    continue
                count = groups.get(event, 0)
                if self.kind == "keyboard" and count:
                    continue
                groups[event] = count + 1
                filename = f"{event}.wav" if count == 0 else f"{event}__{count:03d}.wav"
                shutil.copyfile(path, folder / filename)
            if not groups:
                raise ValueError("The selected source has no WAV events for this sound pack category")
            return identifier
        except Exception:
            shutil.rmtree(folder)
            raise

    def import_legacy_folder(self, folder: Path, name: str, roles=(), states=()) -> str:
        folder = Path(folder)
        if not folder.is_dir():
            raise ValueError("The selected folder does not exist")
        files = [p for p in folder.rglob("*.wav") if p.is_file()]
        if len(files) > MAX_FILES:
            raise ValueError("Too many sound files")
        groups = {path.relative_to(folder).parts[0] for path in files
                  if len(path.relative_to(folder).parts) > 1}
        if self.kind in ("typing", "keyboard") and len(groups) > 1:
            raise ValueError("Choose one sound pack folder, not a parent containing multiple packs")
        return self._import_files([(p, p.stem) for p in files], name, roles, states)

    def export_zip(self, theme_id: str, destination: Path):
        folder = self.directory(theme_id)
        self.load(theme_id)
        with ZipFile(destination, "w", ZIP_DEFLATED) as output:
            for wav in folder.glob("*.wav"):
                output.write(wav, wav.name)

    def import_zip(self, source: Path, name: str) -> str:
        """Import manifest-free packs, or convert v0.2 theme.json ZIPs."""
        import tempfile
        with ZipFile(source) as archive:
            infos = archive.infolist()
            if (len(infos) > MAX_FILES or sum(entry.file_size for entry in infos) > MAX_ZIP_SIZE
                    or any(not self._safe_zip_name(entry.filename) for entry in infos)):
                raise ValueError("Unsafe or oversized sound pack ZIP")
            old_map = None
            if "theme.json" in archive.namelist():
                old_map = json.loads(archive.read("theme.json"))["sounds"]
            with tempfile.TemporaryDirectory(prefix="nvda-sound-import-") as temp:
                root = Path(temp)
                extracted = []
                for entry in infos:
                    if entry.is_dir() or not entry.filename.lower().endswith(".wav"):
                        continue
                    if entry.file_size > MAX_WAV_SIZE:
                        raise ValueError("WAV exceeds 8 MB")
                    target = root / f"{len(extracted):04d}.wav"
                    with archive.open(entry) as original, target.open("wb") as writable:
                        shutil.copyfileobj(original, writable)
                    extracted.append((entry.filename, target))
                if not extracted:
                    raise ValueError("Sound pack ZIP contains no WAV files")
                if old_map is not None:
                    named = []
                    for event, ref in old_map.items():
                        if not EVENT_PATTERN.fullmatch(event) or not self.accepts(event):
                            continue
                        values = ref if isinstance(ref, list) else [ref]
                        for relative in values:
                            named.extend((file, event) for original, file in extracted if original == relative)
                else:
                    dirs = {str(Path(original).parent) for original, _ in extracted}
                    if len(dirs) > 1:
                        raise ValueError("Choose one sound pack ZIP, not an archive of several packs")
                    named = [(file, Path(original).stem) for original, file in extracted]
                return self._import_files(named, name)

    def migrate_previous_themes(self, old_root: Path) -> int:
        """Convert v0.1 mixed manifest packs to sound folders; preserve originals."""
        if self.kind == "mixed" or not old_root.is_dir():
            return 0
        count = 0
        for source in old_root.iterdir():
            manifest = source / "theme.json"
            if not manifest.is_file():
                continue
            try:
                info = json.loads(manifest.read_text(encoding="utf-8"))
                name = str(info.get("name") or source.name)
                identifier = "user:" + safe_slug(name)
                if self.directory(identifier).exists():
                    continue
                files = []
                for event, names in info["sounds"].items():
                    if not EVENT_PATTERN.fullmatch(event) or not self.accepts(event):
                        continue
                    for relative in (names if isinstance(names, list) else [names]):
                        if not self._safe_zip_name(relative):
                            continue
                        path = (source / relative).resolve()
                        if path.is_relative_to(source.resolve()) and path.is_file():
                            files.append((path, event))
                self._import_files(files, name)
                count += 1
            except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return count

    def migrate_manifest_packs(self) -> int:
        """Convert user v0.2 packs in place, backing up complete source dirs."""
        if not self.writable.is_dir():
            return 0
        count = 0
        backup = self.writable.parent.parent / "legacy-backups" / self.kind
        for folder in list(self.writable.iterdir()):
            manifest = folder / "theme.json"
            if not manifest.is_file():
                continue
            try:
                info = json.loads(manifest.read_text(encoding="utf-8"))
                refs = []
                for event, names in info["sounds"].items():
                    if not EVENT_PATTERN.fullmatch(event) or not self.accepts(event):
                        continue
                    for relative in (names if isinstance(names, list) else [names]):
                        if not self._safe_zip_name(relative):
                            continue
                        path = (folder / relative).resolve()
                        if path.is_relative_to(folder.resolve()) and path.is_file():
                            refs.append((relative, event))
                backup.mkdir(parents=True, exist_ok=True)
                destination = backup / folder.name
                if destination.exists():
                    continue
                folder.rename(destination)
                try:
                    new_files = [(destination / rel, event) for rel, event in refs]
                    self._import_files(new_files, folder.name)
                except Exception:
                    if folder.exists():
                        shutil.rmtree(folder)
                    destination.rename(folder)
                    raise
                count += 1
            except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return count
