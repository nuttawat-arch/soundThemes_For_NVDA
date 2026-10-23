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


class KeyboardState:
    def __init__(self):
        self._pressed = set()
        self._last_navigation_press = 0.0
        self._lock = RLock()

    def update(self, vk: int, down: bool) -> bool:
        """Return True only for first keydown. Repeated keydown is ignored."""
        with self._lock:
            first = vk not in self._pressed
            if down:
                self._pressed.add(vk)
                if vk in NAV_KEYS:
                    self._last_navigation_press = time.monotonic()
            else:
                self._pressed.discard(vk)
            return bool(down and first)

    def is_pressed(self, vk: int) -> bool:
        with self._lock:
            return vk in self._pressed

    def clear(self):
        with self._lock:
            self._pressed.clear()
            self._last_navigation_press = 0.0

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
