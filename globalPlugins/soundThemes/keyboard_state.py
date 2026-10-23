"""Non-blocking pressed-key tracking inspired by ScreenReaderSounds' k.is_pressed.

The original k (keyboard 0.13.5) creates an independent global low-level
keyboard hook and background listeners. NVDA already owns a hook. Listening
to NVDA's public raw-key decider gives us the same pressed-key knowledge
without installing a second hook, injecting keys or blocking input.
"""

from __future__ import annotations

from threading import RLock
import time

NAV_KEYS = {
    0x09: "key.tab", 0x21: "key.page", 0x22: "key.page",
    0x23: "key.home_end", 0x24: "key.home_end",
    0x25: "key.left", 0x26: "key.up", 0x27: "key.right", 0x28: "key.down",
}
MEDIA_KEYS = frozenset({0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2, 0xB3})


def physical_virtual_key(vk: int, scan_code: int | None = None,
                         extended: bool = False) -> int:
    """Collapse generic and side-specific modifier reports onto ONE physical key.

    Some Windows keyboard drivers report both VK_SHIFT and VK_LSHIFT for a
    single press. Otherwise the generic and side-specific bindings can each
    play a separate WAV. Windows scan codes identify left/right Shift, while
    the extended bit identifies right Control and Alt.
    """
    if vk == 0x10:
        return 0xA1 if scan_code == 0x36 else 0xA0
    if vk == 0x11:
        return 0xA3 if extended else 0xA2
    if vk == 0x12:
        return 0xA5 if extended else 0xA4
    return vk


class KeyboardState:
    def __init__(self):
        self._pressed = set()
        self._last_navigation_press = 0.0
        self._last_shift_press = 0.0
        self._last_typing_special = {}
        self._lock = RLock()

    def update(self, vk: int, down: bool) -> bool:
        """Return True only for first keydown. Repeated keydown is ignored."""
        with self._lock:
            first = vk not in self._pressed
            if down:
                self._pressed.add(vk)
                if vk in NAV_KEYS:
                    self._last_navigation_press = time.monotonic()
                if vk in (0x10, 0xA0, 0xA1):
                    self._last_shift_press = time.monotonic()
            else:
                self._pressed.discard(vk)
            return bool(down and first)

    def update_physical(self, vk: int, scan_code: int | None,
                        extended: bool, down: bool) -> tuple[bool, int]:
        """Track raw key transitions under their side-specific physical code."""
        physical = physical_virtual_key(vk, scan_code, extended)
        return self.update(physical, down), physical

    def is_pressed(self, vk: int) -> bool:
        with self._lock:
            if vk == 0x10:
                return vk in self._pressed or 0xA0 in self._pressed or 0xA1 in self._pressed
            if vk == 0x11:
                return vk in self._pressed or 0xA2 in self._pressed or 0xA3 in self._pressed
            if vk == 0x12:
                return vk in self._pressed or 0xA4 in self._pressed or 0xA5 in self._pressed
            return vk in self._pressed

    def clear(self):
        with self._lock:
            self._pressed.clear()
            self._last_navigation_press = 0.0
            self._last_shift_press = 0.0
            self._last_typing_special.clear()

    def note_typing_special(self, event: str):
        """Remember a raw-key cue to avoid replay on typedCharacter callback."""
        with self._lock:
            self._last_typing_special[event] = time.monotonic()

    def consume_typing_special(self, event: str, max_age: float = 0.5) -> bool:
        """Consume one recent matching raw-key cue, not unrelated typing."""
        with self._lock:
            at = self._last_typing_special.pop(event, None)
            return at is not None and time.monotonic() - at <= max_age

    def shift_recent(self, max_age: float = 0.35) -> bool:
        """Detect NVDA's Shift-to-pause gesture even after the key is released."""
        with self._lock:
            return self.is_pressed(0x10) or bool(
                self._last_shift_press and
                time.monotonic() - self._last_shift_press <= max_age
            )

    def navigation_recent(self, max_age: float = 0.25) -> bool:
        """True for a genuine recent navigation keystroke, not typed text."""
        with self._lock:
            return bool(self._last_navigation_press and
                        time.monotonic() - self._last_navigation_press <= max_age)

    def event_for_key(self, vk: int) -> str | None:
        if vk == 0x09 and self.is_pressed(0x10):
            return "key.shift_tab"
        if vk in NAV_KEYS:
            return NAV_KEYS[vk]
        if vk in MEDIA_KEYS:
            return "system.media"
        if vk in (0x08, 0x2E):
            return "key.backspace"
        if vk == 0x20:
            return "key.space"
        if vk == 0x0D:
            return "key.enter"
        if vk == 0x1B:
            return "nav.close"
        return None
