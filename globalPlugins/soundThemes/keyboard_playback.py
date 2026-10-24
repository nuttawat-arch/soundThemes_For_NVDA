"""Per-preset two-layer or single-file keyboard sounds, without extra hooks."""

KEYBOARD_PLAYBACK_MODES = ("separate", "combined")


def normalize_mode(mode: str) -> str:
    """Treat old keydown-only preferences as single-file mode, losslessly."""
    return "separate" if mode == "separate" else "combined"


def cue_for_transition(event: str, pressed: bool, changed: bool, mode: str) -> str | None:
    if not changed:
        return None
    if pressed:
        return event
    if mode == "separate":
        return event + ".release"
    return None
