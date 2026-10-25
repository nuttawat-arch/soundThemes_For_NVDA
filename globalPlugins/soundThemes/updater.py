"""Opt-in, user-confirmed Sound Themes updates from official GitHub Releases.

No NVDA Add-on Store submission is needed. All HTTP/file work runs on daemon
workers; only dialogs, speech feedback and the NVDA installer run on wx's UI
thread. Nothing installs automatically or consumes keyboard events.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import urllib.request
from urllib.parse import urlsplit

import addonHandler
import config
import gui
import globalVars
import ui
import wx
from logHandler import log

from .release_info import (CHECK_INTERVAL_MINUTES, LATEST_RELEASE_URL,
                           MAX_INSTALLER_BYTES, release_state, validated_release)

addonHandler.initTranslation()


TIMEOUT_SECONDS = 20
STARTUP_DELAY_MS = 15000
SECTION = "soundThemes"


def update_check_interval_ms(value) -> int:
    """Coerce imported settings into a safe, API-friendly polling interval."""
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        minutes = 30
    return (minutes if minutes in CHECK_INTERVAL_MINUTES else 30) * 60 * 1000


def _request(url: str):
    return urllib.request.Request(url, headers={
        "User-Agent": "SoundThemesForNVDA-update-checker",
        "Accept": "application/vnd.github+json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })


def _installed_version() -> str:
    try:
        return str(addonHandler.getCodeAddon().version)
    except (AttributeError, RuntimeError):
        return "0.0.0"


def _managed_by_store() -> bool:
    try:
        return getattr(addonHandler.getCodeAddon(), "_addonStoreData", None) is not None
    except (AttributeError, RuntimeError):
        return False


def _download_installer(release) -> str:
    fd, destination = tempfile.mkstemp(prefix="soundthemes-update-", suffix=".nvda-addon")
    digest = hashlib.sha256()
    total = 0
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(
            _request(release.download_url), timeout=TIMEOUT_SECONDS
        ) as response:
            final_url = urlsplit(response.geturl())
            if (final_url.scheme != "https" or
                    (final_url.netloc.lower() != "github.com" and
                     not final_url.netloc.lower().endswith(".githubusercontent.com"))):
                raise ValueError("Update download redirected outside GitHub")
            while True:
                block = response.read(65536)
                if not block:
                    break
                total += len(block)
                if total > MAX_INSTALLER_BYTES:
                    raise ValueError("Update installer exceeds the size limit")
                digest.update(block)
                out.write(block)
        if total == 0:
            raise ValueError("The update installer was empty")
        if release.sha256 is not None and digest.hexdigest().lower() != release.sha256:
            raise ValueError("Update installer SHA-256 checksum mismatch")
        return destination
    except Exception:
        try:
            os.unlink(destination)
        except OSError:
            pass
        raise


class ReleaseNotesDialog(wx.Dialog):
    """Accessible read-only change log with explicit update/delay/skip choices."""

    def __init__(self, parent, installed, release):
        super().__init__(parent, title=_("Sound Themes update"), size=(720, 560),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main = wx.BoxSizer(wx.VERTICAL)
        headline = _(
            "Sound Themes {new} is available (installed: {old})."
        ).format(new=release.version, old=installed)
        main.Add(wx.StaticText(self, label=headline), 0, wx.ALL | wx.EXPAND, 10)
        main.Add(wx.StaticText(self, label=_("What's new in this version:")),
                 0, wx.LEFT | wx.RIGHT, 10)
        notes = release.notes or _("No release notes were provided for this version.")
        self.notes = wx.TextCtrl(self, value=notes,
                                 style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.notes.SetName(_("What's new in Sound Themes %s") % release.version)
        main.Add(self.notes, 1, wx.EXPAND | wx.ALL, 10)
        main.Add(wx.StaticText(self, label=_(
            "Your customized WAV sounds will be preserved during a normal NVDA "
            "add-on update. Export a ZIP backup if you want an extra copy. "
            "NVDA will ask before installation."
        )), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        actions = wx.BoxSizer(wx.HORIZONTAL)
        for identifier, label in (
            (wx.ID_YES, _("&Update now")),
            (wx.ID_NO, _("&Later")),
            (wx.ID_CANCEL, _("&Skip this version")),
        ):
            button = wx.Button(self, identifier, label)
            button.Bind(wx.EVT_BUTTON, lambda evt, choice=identifier: self.EndModal(choice))
            actions.Add(button, 0, wx.RIGHT, 6)
        main.Add(actions, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizer(main)
        self.SetEscapeId(wx.ID_NO)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.EndModal(wx.ID_NO)  # Window Close is Later, never Skip.


class UpdateChecker:
    def __init__(self):
        self._lock = threading.Lock()
        self._busy = False
        self._closed = False
        self._timer = None

    def configure_auto_checks(self):
        """Apply settings immediately, without asking the user to restart NVDA."""
        if self._timer is not None:
            self._timer.Stop()
            self._timer = None
        if (not self._closed and not _managed_by_store()
                and not getattr(globalVars.appArgs, "secure", False)
                and config.conf[SECTION]["checkForUpdates"]):
            self._timer = wx.CallLater(STARTUP_DELAY_MS, self._periodic_tick)

    def _periodic_tick(self):
        if self._closed:
            return
        if _managed_by_store() or not config.conf[SECTION]["checkForUpdates"]:
            self._timer = None
            return
        self.check(manual=False)
        interval = update_check_interval_ms(config.conf[SECTION]["updateCheckIntervalMinutes"])
        self._timer = wx.CallLater(interval, self._periodic_tick)

    def terminate(self):
        with self._lock:
            self._closed = True
        if self._timer is not None:
            self._timer.Stop()
            self._timer = None

    def check(self, manual: bool = False):
        with self._lock:
            if self._busy or self._closed:
                if manual and not self._closed:
                    wx.CallAfter(ui.message, _("A Sound Themes update check is already running."))
                return
            if not manual and (_managed_by_store() or not config.conf[SECTION]["checkForUpdates"]):
                return
            self._busy = True
        if manual:
            ui.message(_("Checking for Sound Themes updates..."))
        threading.Thread(target=self._check_worker, args=(manual,),
                         name="SoundThemes.checkUpdates", daemon=True).start()

    def _check_worker(self, manual):
        try:
            with urllib.request.urlopen(_request(LATEST_RELEASE_URL), timeout=TIMEOUT_SECONDS) as response:
                release = validated_release(json.load(response))
            installed = _installed_version()
            state = release_state(installed, release)
        except Exception:
            log.warning("Sound Themes: update check unavailable", exc_info=True)
            wx.CallAfter(self._notify, _("Could not check Sound Themes updates.")) if manual else None
            return
        finally:
            with self._lock:
                self._busy = False
        if state == "unavailable":
            if manual:
                wx.CallAfter(self._notify, _(
                    "No Sound Themes update is ready to download yet. Please try again later."))
            return
        if state == "not_published":
            if manual:
                wx.CallAfter(self._notify, _(
                    "Sound Themes %s is installed, but the latest downloadable release is %s. "
                    "A newer update may still be publishing. Please check again shortly."
                ) % (installed, release.version))
            return
        if state == "current":
            if manual:
                wx.CallAfter(self._notify, _("Sound Themes %s is up to date.") % installed)
            return
        if not manual and release.version == config.conf[SECTION]["skippedUpdateVersion"]:
            return
        if not manual and release.version == config.conf[SECTION]["lastNotifiedUpdateVersion"]:
            return
        wx.CallAfter(self._offer, installed, release)

    def _notify(self, message):
        if not self._closed:
            ui.message(message)

    def _offer(self, installed, release):
        if self._closed:
            return
        dialog = ReleaseNotesDialog(gui.mainFrame, installed, release)
        # Record before opening the modal window so a later timer cannot queue
        # the same version again while this dialog is still being read.
        config.conf[SECTION]["lastNotifiedUpdateVersion"] = release.version
        gui.mainFrame.prePopup()
        try:
            wx.CallAfter(dialog.notes.SetFocus)
            answer = dialog.ShowModal()
        finally:
            dialog.Destroy()
            gui.mainFrame.postPopup()
        if answer == wx.ID_YES:
            ui.message(_("Downloading Sound Themes %s...") % release.version)
            threading.Thread(target=self._install_worker, args=(release,),
                             name="SoundThemes.downloadUpdate", daemon=True).start()
        elif answer == wx.ID_CANCEL:
            config.conf[SECTION]["skippedUpdateVersion"] = release.version

    def _install_worker(self, release):
        try:
            destination = _download_installer(release)
        except Exception:
            log.warning("Sound Themes: update download failed", exc_info=True)
            wx.CallAfter(self._notify, _("Could not download or verify the Sound Themes update."))
            return
        if self._closed:
            try:
                os.unlink(destination)
            except OSError:
                pass
            return
        from gui import addonGui
        wx.CallAfter(addonGui.handleRemoteAddonInstall, destination)
