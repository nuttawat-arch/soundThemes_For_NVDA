"""Public sound event vocabulary; independent from the NVDA runtime."""

from __future__ import annotations

import re


EVENT_GROUPS = {
    "System": {
        "system.start": "NVDA started", "system.stop": "NVDA stopping",
        "system.lock": "Windows session locked (first cue)",
        "system.lockscreen": "Windows lock screen (second cue)",
        "system.unlock": "Windows session unlocked",
        "system.secure_enter": "Secure desktop entered",
        "system.secure_exit": "Secure desktop left",
        "system.app_open": "Application opened / Explorer entered",
        "system.app_close": "Application closed / Explorer left",
        "system.app_switch": "Application switched",
        "system.window": "Foreground window", "system.alert": "Alert",
        "system.notification": "Notification", "system.media": "Media control",
        "system.error": "Error",
        "system.ready": "ScreenReaderSounds ready", "system.complete": "Document finished loading",
        "system.paused_feedback": "Speech feedback paused (when supported)",
        "system.tutorial": "Tutorial shortcut (when supported)",
        "system.volume_beep": "System volume feedback (when supported)",
    },
    "Keyboard": {
        "key.character": "Character typed", "key.space": "Space",
        "key.backspace": "Backspace / Delete", "key.protected": "Password character",
        "key.enter": "Enter / activation", "key.tab": "Tab / forward",
        "key.shift_tab": "Shift+Tab / backward", "key.up": "Up arrow",
        "key.down": "Down arrow", "key.left": "Left arrow",
        "key.right": "Right arrow", "key.page": "Page Up / Page Down",
        "key.home_end": "Home / End", "key.boundary": "Text boundary",
        "key.invalid": "Invalid navigation",
    },
    "Navigation": {
        "nav.focus": "Focus moved", "nav.browse": "Browse mode moved",
        "nav.quick": "Quick navigation", "nav.caret": "Caret moved",
        "nav.mouse": "Mouse hover", "nav.selection": "Selection changed",
        "nav.empty": "Unnamed / empty object", "nav.edit_exit": "Leaving edit/document",
        "nav.scroll": "Scrolled", "nav.open": "Item opened",
        "nav.close": "Item closed", "nav.expand": "Expanded",
        "nav.collapse": "Collapsed", "nav.activate": "Activated / clicked",
        "nav.long_activate": "Long press / long click (when supported)",
        "nav.tick": "Selection tick",
    },
    "Object events": {
        "object.foreground": "Foreground changed", "object.focus_entered": "Focus entered",
        "object.focus_lost": "Focus lost", "object.state": "State changed",
        "object.value": "Value changed", "object.name": "Name changed",
        "object.description": "Description changed",
        "object.show": "Object appeared", "object.hide": "Object disappeared",
        "object.document": "Document loaded", "object.text": "Text changed",
        "object.live": "Live region", "object.location": "Location changed",
    },
}

# Physical typing packs are deliberately isolated from navigation packs.
# Keys that move focus or the caret (Tab, arrows, Page Up/Down, Home/End)
# are navigation effects, not character typing effects.
TYPING_EVENTS = frozenset({
    "key.character", "key.space", "key.backspace", "key.protected", "key.enter",
})


def is_typing_event(event: str) -> bool:
    return event in TYPING_EVENTS


def is_keyboard_event(event: str) -> bool:
    return event.startswith("keyboard.")


def canonical_name(value: object) -> str:
    """Unify Enum role/state names across modern NVDA releases."""
    name = getattr(value, "name", str(value))
    return re.sub(r"[^a-z0-9]", "", name.lower())


def all_events(roles=(), states=()):
    """Sorted (group, key, accessible label) tuples; add every runtime Role/State."""
    entries = [(group, key, label) for group, group_events in EVENT_GROUPS.items()
               for key, label in group_events.items()]
    for role in roles:
        name = canonical_name(role)
        if name:
            entries.append(("NVDA roles", f"role.{name}", str(getattr(role, 'name', name))))
    for state in states:
        name = canonical_name(state)
        if name:
            entries.append(("NVDA states", f"state.{name}", str(getattr(state, 'name', name))))
    entries.append(("NVDA roles", "role.default", "Any other role (fallback)"))
    entries.append(("NVDA states", "state.default", "Any other state (fallback)"))
    return sorted(entries, key=lambda row: (row[0], row[2].casefold()))


LEGACY_EVENTS = {
    "tab": "key.tab", "shifttab": "key.shift_tab", "clicked": "nav.activate",
    "media": "system.media", "scroll": "nav.scroll",
    "typekey": "key.character", "typekeyspace": "key.space",
    "typekeypr": "key.protected", "typekeyremove": "key.backspace",
    "closed": "nav.close", "opened": "nav.open", "notext": "nav.empty",
    "collapsed": "nav.collapse", "expanded": "nav.expand",
    "eclose": "nav.edit_exit", "delete": "key.backspace",
    "lock": "system.lock", "lockscreen": "system.lockscreen",
    "unlockscreen": "system.unlock", "error": "key.invalid",
    "end": "key.home_end", "space": "key.space",
}


def legacy_event_for_filename(stem: str, role_names=(), state_names=()) -> str | None:
    """Map ScreenReaderSounds / navSounds WAV filenames to the new format."""
    key = canonical_name(stem)
    if key in LEGACY_EVENTS:
        return LEGACY_EVENTS[key]
    if key in {canonical_name(role) for role in role_names}:
        return f"role.{key}"
    if key in {canonical_name(state) for state in state_names}:
        return f"state.{key}"
    return None


def candidates(event_key: str) -> tuple[str, ...]:
    """Choose an exact binding first; then cover unknown future NVDA roles/states."""
    if event_key == "keyboard.shift_tab":
        return (event_key, "keyboard.tab", "keyboard.default")
    if event_key.startswith("keyboard.") and event_key != "keyboard.default":
        # A real recording from this same keyboard pack may serve keys the
        # source recording set does not cover (e.g. F13 or volume keys).
        return (event_key, "keyboard.default")
    if event_key.startswith("role."):
        return (event_key, "role.default", "nav.focus")
    if event_key.startswith("state."):
        return (event_key, "state.default", "object.state")
    return (event_key,)
