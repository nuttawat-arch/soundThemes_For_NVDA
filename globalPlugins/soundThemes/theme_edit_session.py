"""Reversible sound-pack editing; Done commits and Cancel restores WAVs."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path


def _same_file_bytes(left: Path, right: Path) -> bool:
    """Compare WAVs without filecmp, which is absent in NVDA's bundled Python.

    This runs only when closing an editor with a prepared rollback snapshot;
    never on the keyboard/audio event handling threads.
    """
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as before, right.open("rb") as after:
        while True:
            a = before.read(131072)
            b = after.read(131072)
            if a != b:
                return False
            if not a:
                return True


class ThemeEditSession:
    def __init__(self, store, identifier: str):
        self.folder = Path(store.directory(identifier))
        self._temp = None
        self._backup = None

    def prepare_edit(self):
        """Snapshot lazily, so merely opening or browsing is instantaneous."""
        if self._temp is None:
            temporary = tempfile.TemporaryDirectory(prefix="nvda-theme-edit-")
            try:
                backup = Path(temporary.name) / "original"
                shutil.copytree(self.folder, backup)
            except Exception:
                temporary.cleanup()
                raise
            self._temp = temporary
            self._backup = backup

    def commit(self):
        if self._temp is not None:
            self._temp.cleanup()
            self._temp = None
            self._backup = None

    def has_changes(self) -> bool:
        """Detect pending changes without prompting after merely browsing sounds."""
        if self._backup is None:
            return False
        if not self.folder.is_dir():
            return True

        def files_in(root):
            return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}

        before = files_in(self._backup)
        after = files_in(self.folder)
        if before != after:
            return True
        return any(not _same_file_bytes(self._backup / path, self.folder / path)
                   for path in before)

    def rollback(self):
        """Restore exact original files; preserve the working copy on errors."""
        if self._backup is None:
            return False
        displaced = self.folder.with_name(self.folder.name + ".cancel-" + uuid.uuid4().hex[:8])
        self.folder.rename(displaced)
        try:
            shutil.copytree(self._backup, self.folder)
        except Exception:
            if self.folder.exists():
                shutil.rmtree(self.folder)
            displaced.rename(self.folder)
            raise
        else:
            shutil.rmtree(displaced)
            self.commit()
            return True
