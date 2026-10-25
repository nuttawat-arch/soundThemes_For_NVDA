"""Keep personal WAV edits when NVDA stages an update to Sound Themes.

NVDA calls onInstall from the freshly extracted ``.pendingInstall`` add-on
directory, while the previously installed add-on still exists beside it.
No NVDA imports, network access, user configuration copies or UI are needed.

An installed stock-audio manifest allows distinguishing personal edits from
unmodified bundled audio. Older versions have no manifest; for the first
upgrade we favor protecting every existing WAV rather than risking data loss.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid


EFFECTS = Path("globalPlugins") / "soundThemes" / "effects"
STOCK_MANIFEST = "soundthemes-stock-wavs.json"
CATEGORIES = frozenset(("navigation", "typing", "keyboard"))
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_relative(value: str) -> Path | None:
    """Accept relative paths to category/theme/*.wav, never traversal."""
    if not isinstance(value, str) or "\\" in value or ":" in value:
        return None
    relative = Path(value)
    if (relative.is_absolute() or len(relative.parts) < 3 or
            relative.parts[0] not in CATEGORIES or
            any(part in ("", ".", "..") for part in relative.parts) or
            relative.suffix.lower() != ".wav"):
        return None
    return relative


def _original_hashes(previous: Path) -> dict[str, str] | None:
    manifest = previous / STOCK_MANIFEST
    if not manifest.is_file() or manifest.is_symlink() or manifest.stat().st_size > 1024 * 1024:
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        entries = data["files"]
        if data.get("schema") != 1 or not isinstance(entries, dict):
            return None
        if any(_safe_relative(name) is None or not isinstance(hash_, str) or
               not _SHA256.fullmatch(hash_) for name, hash_ in entries.items()):
            return None
        return entries
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _copy_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".soundthemes-" + uuid.uuid4().hex + ".tmp")
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def preserve_personal_wavs(previous_addon: Path, pending_addon: Path) -> dict[str, int]:
    """Merge old personal audio into the pending update, not the running add-on.

    Never delete anything from the old installation. If reading or copying
    personal WAVs fails, propagate the exception: NVDA must abort the update
    rather than silently replace an edit it was supposed to protect.
    """
    old_root = Path(previous_addon) / EFFECTS
    new_root = Path(pending_addon) / EFFECTS
    result = {"copied": 0, "kept_new_stock": 0, "deleted": 0, "removed_packs": 0}
    if not old_root.is_dir():
        return result
    if not new_root.is_dir():
        raise FileNotFoundError("The update has no sound folder; refusing to discard existing WAVs")
    if new_root.is_symlink():
        raise ValueError("The staged sound folder must not be a symbolic link")

    baseline = _original_hashes(Path(previous_addon))
    # Only transfer WAV files from the three actual sound-pack categories.
    # This also retains manually imported packs and historical _unused WAVs.
    for kind in sorted(CATEGORIES):
        old_category = old_root / kind
        if not old_category.is_dir() or old_category.is_symlink():
            continue
        for source in sorted(old_category.rglob("*")):
            if not source.is_file() or source.is_symlink() or source.suffix.lower() != ".wav":
                continue
            rel = source.relative_to(old_root)
            key = rel.as_posix()
            if _safe_relative(key) is None:
                continue
            if baseline is not None and baseline.get(key) == _sha256(source):
                result["kept_new_stock"] += 1
                continue
            destination = new_root / rel
            # A malicious/replaced symlink in the pending tree must not escape
            # the extracted add-on directory or alter an external WAV.
            if any(part.is_symlink() for part in (destination, *destination.parents)
                   if part == new_root or new_root in part.parents):
                raise ValueError("Update destination contains a symbolic link")
            _copy_atomic(source, destination)
            result["copied"] += 1

    # A deleted stock recording is also a user edit. Reapply that removal only
    # when its original preset folder still exists. A deliberately deleted
    # whole preset should stay absent, including newly shipped files within
    # that preset. The NVDA removed*Presets configuration is preserved outside
    # the add-on as an additional guard against reviving removed preset names.
    if baseline is not None:
        stock_packs: set[Path] = set()
        for key in baseline:
            rel = _safe_relative(key)
            if rel is None:
                continue
            stock_packs.add(Path(rel.parts[0]) / rel.parts[1])
            previous_file = old_root / rel
            previous_pack = old_root / rel.parts[0] / rel.parts[1]
            installed_file = new_root / rel
            if (previous_pack.is_dir() and not previous_pack.is_symlink() and
                    not previous_file.exists() and not previous_file.is_symlink() and
                    installed_file.is_file() and not installed_file.is_symlink()):
                installed_file.unlink()
                result["deleted"] += 1

        for pack_rel in sorted(stock_packs):
            old_pack = old_root / pack_rel
            new_pack = new_root / pack_rel
            if (not old_pack.exists() and not old_pack.is_symlink()
                    and new_pack.is_dir() and not new_pack.is_symlink()):
                if new_pack.parent.is_symlink():
                    raise ValueError("Staged preset has a symbolic-link parent")
                shutil.rmtree(new_pack)
                result["removed_packs"] += 1

    return result


def onInstall() -> None:
    """NVDA add-on installation entry point, before the version switch."""
    pending = Path(__file__).resolve().parent
    suffix = ".pendingInstall"
    if not pending.name.endswith(suffix):
        return
    previous = pending.with_name(pending.name[:-len(suffix)])
    if previous.is_dir() and not previous.is_symlink():
        preserve_personal_wavs(previous, pending)
