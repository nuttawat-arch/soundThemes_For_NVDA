"""Pure, offline-testable validation of Sound Themes GitHub releases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote, urlsplit


REPOSITORY = "nuttawat-arch/soundThemes_For_NVDA"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
MAX_INSTALLER_BYTES = 150 * 1024 * 1024
CHECK_INTERVAL_MINUTES = (10, 30, 60, 180, 360, 720, 1440)
_VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)", re.IGNORECASE)


def version_key(value: str) -> tuple[int, int, int]:
    match = _VERSION.fullmatch(str(value).strip())
    if not match:
        raise ValueError("Invalid Sound Themes release version")
    return tuple(int(group) for group in match.groups())


def is_newer(candidate: str, current: str) -> bool:
    return version_key(candidate) > version_key(current)


@dataclass(frozen=True)
class Release:
    version: str
    page: str
    download_url: str
    sha256: str | None
    notes: str = ""


def release_state(installed: str, release: Release | None) -> str:
    """Distinguish installed/current/pending publications for truthful status UI."""
    if release is None:
        return "unavailable"
    if is_newer(release.version, installed):
        return "update"
    if is_newer(installed, release.version):
        return "not_published"
    return "current"


def validated_release(payload: dict) -> Release | None:
    """Trust only a stable release's named add-on from our exact repository.

    GitHub may supply a sha256 asset digest. Reject unrelated assets, untrusted
    redirects listed in metadata, and malformed versions before any download.
    """
    if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
        return None
    tag = payload.get("tag_name", "")
    if not isinstance(tag, str):
        return None
    try:
        key = version_key(tag)
    except ValueError:
        return None
    version = ".".join(str(part) for part in key)
    expected_name = f"SoundThemesForNVDA-{version}.nvda-addon"
    expected_path = f"/{REPOSITORY}/releases/download/{quote(tag, safe='')}/{expected_name}"
    for asset in payload.get("assets", ()):
        if not isinstance(asset, dict) or asset.get("name") != expected_name:
            continue
        url = asset.get("browser_download_url", "")
        parsed = urlsplit(url) if isinstance(url, str) else urlsplit("")
        if (parsed.scheme != "https" or parsed.netloc.lower() != "github.com"
                or parsed.path != expected_path or parsed.query or parsed.fragment):
            continue
        size = asset.get("size")
        if size is not None and (not isinstance(size, int) or not 0 < size <= MAX_INSTALLER_BYTES):
            continue
        digest = asset.get("digest", "")
        sha256 = None
        if isinstance(digest, str) and digest.startswith("sha256:"):
            value = digest.removeprefix("sha256:")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", value):
                continue
            sha256 = value.lower()
        page = payload.get("html_url", "")
        page_parts = urlsplit(page) if isinstance(page, str) else urlsplit("")
        if (page_parts.scheme != "https" or page_parts.netloc.lower() != "github.com"
                or page_parts.path != f"/{REPOSITORY}/releases/tag/{tag}"):
            page = f"https://github.com/{REPOSITORY}/releases/tag/{tag}"
        body = payload.get("body", "")
        if not isinstance(body, str):
            body = ""
        notes = "".join(char for char in body if char in "\n\t" or ord(char) >= 32).strip()
        return Release(version, page, url, sha256, notes[:12000])
    return None
