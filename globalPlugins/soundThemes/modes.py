"""Exclusive keyboard / navigation+typing mode rules without wx/NVDA imports."""

from __future__ import annotations


def resolve_modes(navigation: bool, typing: bool, keyboard: bool, changed: str = ""):
    """Keyboard mode owns all keydown sounds and excludes both other modes."""
    if changed == "keyboard" and keyboard:
        return False, False, True
    if changed in ("navigation", "typing") and (navigation or typing):
        return navigation, typing, False
    if keyboard:
        return False, False, True
    return navigation, typing, False
