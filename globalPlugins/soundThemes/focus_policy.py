"""Focus cue selection, independent of NVDA and GUI framework."""

from __future__ import annotations

from .catalog import canonical_name


def cue_for_focus(role, states, has_exact_sound) -> str:
    """Only let a state override a role when that state has a real WAV.

    In particular State.SELECTED is ubiquitous in Explorer and must not mask
    role.listitem / role.treeviewitem. A bare state fallback is too generic.
    """
    preferred = ("expanded", "collapsed", "checked", "on", "unchecked", "pressed", "protected", "readonly")
    names = {canonical_name(state) for state in (states or ())}
    for name in preferred:
        if name in names and has_exact_sound("state." + name):
            return "state." + name
    if role is not None:
        return "role." + canonical_name(role)
    return "nav.focus"
