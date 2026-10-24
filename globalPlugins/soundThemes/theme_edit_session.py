"""Reversible sound-pack editing; Done commits and Cancel restores WAVs."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path


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
