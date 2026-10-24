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
import ui
import wx
from logHandler import log

from .release_info import LATEST_RELEASE_URL, MAX_INSTALLER_BYTES, is_newer, validated_release

addonHandler.initTranslation()


TIMEOUT_SECONDS = 20
STARTUP_DELAY_MS = 15000
SECTION = "soundThemes"


def _request(url: str):
    return urllib.request.Request(url, headers={
        "User-Agent": "SoundThemesForNVDA-update-checker",
        "Accept": "application/vnd.github+json",
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


class UpdateChecker:
    def __init__(self):
        self._lock = threading.Lock()
        self._busy = False
        self._closed = False

    def terminate(self):
        with self._lock:
            self._closed = True

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
            available = bool(release and is_newer(release.version, installed))
        except Exception:
            log.warning("Sound Themes: update check unavailable", exc_info=True)
            wx.CallAfter(self._notify, _("Could not check Sound Themes updates.")) if manual else None
            return
        finally:
            with self._lock:
                self._busy = False
        if not available:
            if manual:
                wx.CallAfter(self._notify, _("Sound Themes %s is up to date.") % installed)
            return
        if not manual and release.version == config.conf[SECTION]["skippedUpdateVersion"]:
            return
        wx.CallAfter(self._offer, installed, release)

    def _notify(self, message):
        if not self._closed:
            ui.message(message)

    def _offer(self, installed, release):
        if self._closed:
            return
        dialog = wx.MessageDialog(gui.mainFrame, _(
            "Sound Themes {new} is available (installed: {old}).\n\n"
            "Export any customized sound packs to ZIP before updating: "
            "installing a new add-on can overwrite WAV edits stored inside it.\n\n"
            "Download and install it using NVDA's installer? NVDA will ask for confirmation and a restart."
        ).format(new=release.version, old=installed), _("Sound Themes update"),
                                  wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
        dialog.SetYesNoCancelLabels(_("&Update now"), _("&Later"),
                                    _("&Skip this version"))
        gui.mainFrame.prePopup()
        try:
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
