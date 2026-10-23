"""Canonical physical-key identifiers. Independent of NVDA, wx and sound packs.

Windows provides virtual-key codes, not the physical Fn key on many laptops.
Unrecognized VKs retain a stable ``keyboard.vk_xx`` name for custom binding.
"""

from __future__ import annotations


_NAMED = {
    0x01: ("mouse_left", "Left mouse button", "Mouse"),
    0x02: ("mouse_right", "Right mouse button", "Mouse"),
    0x04: ("mouse_middle", "Middle mouse button", "Mouse"),
    0x05: ("mouse_x1", "X1 mouse button", "Mouse"),
    0x06: ("mouse_x2", "X2 mouse button", "Mouse"),
    0x03: ("cancel", "Control+Break", "System keys"),
    0x08: ("backspace", "Backspace", "Editing"),
    0x09: ("tab", "Tab", "Navigation keys"),
    0x0C: ("clear", "Clear", "Editing"),
    0x0D: ("enter", "Enter", "Editing"),
    0x10: ("shift", "Shift (generic)", "Modifiers"),
    0x11: ("ctrl", "Control (generic)", "Modifiers"),
    0x12: ("alt", "Alt (generic)", "Modifiers"),
    0x13: ("pause", "Pause / Break", "System keys"),
    0x14: ("capslock", "Caps Lock", "Locks"),
    0x15: ("ime_kana", "IME Kana", "International"),
    0x16: ("ime_on", "IME On", "International"),
    0x17: ("ime_junja", "IME Junja", "International"),
    0x18: ("ime_final", "IME Final", "International"),
    0x19: ("ime_hanja", "IME Hanja / Kanji", "International"),
    0x1A: ("ime_off", "IME Off", "International"),
    0x1B: ("escape", "Escape", "Navigation keys"),
    0x1C: ("ime_convert", "IME Convert", "International"),
    0x1D: ("ime_nonconvert", "IME Nonconvert", "International"),
    0x1E: ("ime_accept", "IME Accept", "International"),
    0x1F: ("ime_modechange", "IME Mode Change", "International"),
    0x20: ("space", "Space", "Editing"),
    0x21: ("pageup", "Page Up", "Navigation keys"),
    0x22: ("pagedown", "Page Down", "Navigation keys"),
    0x23: ("end", "End", "Navigation keys"),
    0x24: ("home", "Home", "Navigation keys"),
    0x25: ("left", "Left arrow", "Navigation keys"),
    0x26: ("up", "Up arrow", "Navigation keys"),
    0x27: ("right", "Right arrow", "Navigation keys"),
    0x28: ("down", "Down arrow", "Navigation keys"),
    0x29: ("select", "Select", "System keys"),
    0x2A: ("print", "Print", "System keys"),
    0x2B: ("execute", "Execute", "System keys"),
    0x2C: ("printscreen", "Print Screen", "System keys"),
    0x2D: ("insert", "Insert", "Editing"),
    0x2E: ("delete", "Delete", "Editing"),
    0x2F: ("help", "Help", "System keys"),
    0x5B: ("left_windows", "Left Windows", "Modifiers"),
    0x5C: ("right_windows", "Right Windows", "Modifiers"),
    0x5D: ("apps", "Application / Context menu", "System keys"),
    0x5F: ("sleep", "Sleep", "System keys"),
    0x90: ("numlock", "Num Lock", "Locks"),
    0x91: ("scrolllock", "Scroll Lock", "Locks"),
    0xA0: ("left_shift", "Left Shift", "Modifiers"),
    0xA1: ("right_shift", "Right Shift", "Modifiers"),
    0xA2: ("left_ctrl", "Left Control", "Modifiers"),
    0xA3: ("right_ctrl", "Right Control", "Modifiers"),
    0xA4: ("left_alt", "Left Alt", "Modifiers"),
    0xA5: ("right_alt", "Right Alt / AltGr", "Modifiers"),
    0xA6: ("browser_back", "Browser Back", "Media and browser"),
    0xA7: ("browser_forward", "Browser Forward", "Media and browser"),
    0xA8: ("browser_refresh", "Browser Refresh", "Media and browser"),
    0xA9: ("browser_stop", "Browser Stop", "Media and browser"),
    0xAA: ("browser_search", "Browser Search", "Media and browser"),
    0xAB: ("browser_favorites", "Browser Favorites", "Media and browser"),
    0xAC: ("browser_home", "Browser Home", "Media and browser"),
    0xAD: ("volume_mute", "Mute", "Media and browser"),
    0xAE: ("volume_down", "Volume Down", "Media and browser"),
    0xAF: ("volume_up", "Volume Up", "Media and browser"),
    0xB0: ("media_next", "Next Track", "Media and browser"),
    0xB1: ("media_previous", "Previous Track", "Media and browser"),
    0xB2: ("media_stop", "Stop Media", "Media and browser"),
    0xB3: ("media_play_pause", "Play / Pause", "Media and browser"),
    0xB4: ("launch_mail", "Launch Mail", "Media and browser"),
    0xB5: ("launch_media", "Launch Media", "Media and browser"),
    0xB6: ("launch_app1", "Launch Application 1", "Media and browser"),
    0xB7: ("launch_app2", "Launch Application 2", "Media and browser"),
    0xBA: ("semicolon", "Semicolon / Colon", "Punctuation"),
    0xBB: ("equals", "Equals / Plus", "Punctuation"),
    0xBC: ("comma", "Comma", "Punctuation"),
    0xBD: ("minus", "Minus / Underscore", "Punctuation"),
    0xBE: ("period", "Period", "Punctuation"),
    0xBF: ("slash", "Slash / Question mark", "Punctuation"),
    0xC0: ("backtick", "Backtick / Tilde", "Punctuation"),
    0xDB: ("left_bracket", "Left bracket", "Punctuation"),
    0xDC: ("backslash", "Backslash", "Punctuation"),
    0xDD: ("right_bracket", "Right bracket", "Punctuation"),
    0xDE: ("apostrophe", "Apostrophe / Quote", "Punctuation"),
    0xDF: ("oem_8", "OEM 8", "International"),
    0xE2: ("oem_102", "OEM 102 / International backslash", "International"),
    0xE5: ("processkey", "IME Process", "International"),
    0xE7: ("packet", "Unicode Packet", "International"),
    0xF6: ("attn", "Attention", "System keys"),
    0xF7: ("crsel", "Cursor Select", "System keys"),
    0xF8: ("exsel", "Extend Selection", "System keys"),
    0xF9: ("erase_eof", "Erase End of File", "System keys"),
    0xFA: ("play", "Play", "System keys"),
    0xFB: ("zoom", "Zoom", "System keys"),
    0xFC: ("noname", "No Name", "System keys"),
    0xFD: ("pa1", "PA1", "System keys"),
    0xFE: ("oem_clear", "OEM Clear", "System keys"),
}

for _idx in range(10):
    _NAMED[0x30 + _idx] = (str(_idx), str(_idx), "Numbers")
    _NAMED[0x60 + _idx] = (f"numpad_{_idx}", f"Numpad {_idx}", "Numpad")
for _idx in range(26):
    _letter = chr(97 + _idx)
    _NAMED[0x41 + _idx] = (_letter, _letter.upper(), "Letters")
for _idx in range(1, 25):
    _NAMED[0x6F + _idx] = (f"f{_idx}", f"F{_idx}", "Function keys")
for _vk, _slug, _label in (
    (0x6A, "multiply", "Numpad Multiply"),
    (0x6B, "add", "Numpad Add"),
    (0x6C, "separator", "Numpad Separator"),
    (0x6D, "subtract", "Numpad Subtract"),
    (0x6E, "decimal", "Numpad Decimal"),
    (0x6F, "divide", "Numpad Divide"),
):
    _NAMED[_vk] = (_slug, _label, "Numpad")

_EXTRA = {
    "default": ("Fallback recording for unmapped keys in this pack", "Other keys"),
    "numpad_enter": ("Numpad Enter", "Numpad"),
    "shift_tab": ("Shift+Tab", "Navigation keys"),
    "brightness_down": ("Brightness Down / Dim Screen", "Media and browser"),
    "brightness_up": ("Brightness Up", "Media and browser"),
    "fn": ("Fn (only if delivered by Windows)", "System keys"),
}


def event_for_virtual_key(vk: int, scan_code: int | None = None, extended: bool = False) -> str:
    """One stable event per reported key; never choose another sound at random."""
    if not 0 <= int(vk) <= 255:
        raise ValueError("Expected a Windows virtual key in the range 0..255")
    if vk == 0x10 and scan_code in (0x2A, 0x36):
        return "keyboard.right_shift" if scan_code == 0x36 else "keyboard.left_shift"
    if vk == 0x11:
        return "keyboard.right_ctrl" if extended else "keyboard.left_ctrl"
    if vk == 0x12:
        return "keyboard.right_alt" if extended else "keyboard.left_alt"
    if vk == 0x0D and extended:
        return "keyboard.numpad_enter"
    name = _NAMED.get(vk, (f"vk_{vk:02x}", "", ""))[0]
    return "keyboard." + name


def all_keyboard_events():
    """Expose every Windows virtual key, plus common hardware-only bindings."""
    result = []
    for vk in range(1, 256):
        name, label, group = _NAMED.get(vk, (f"vk_{vk:02x}", f"Unknown virtual key 0x{vk:02X}", "Other keys"))
        result.append((group, "keyboard." + name, label))
    result.append(("Numpad", "keyboard.numpad_enter", "Numpad Enter"))
    for name, (label, group) in _EXTRA.items():
        result.append((group, "keyboard." + name, label))
    return sorted(result, key=lambda item: (item[0], item[2].casefold()))


def name_for_event(event: str) -> str:
    return next((label for _, key, label in all_keyboard_events() if key == event), event)
