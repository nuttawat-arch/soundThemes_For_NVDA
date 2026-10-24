"""Resolve browser virtual-caret movements to real NVDA role sound events.

Unlike keyboard focus, Browse Mode can move across buttons, links and headings
without firing ``event_gainFocus``.  Keep this small resolver independent from
NVDA so that it can be tested against real-world event shapes offline.
"""

from __future__ import annotations

from .catalog import canonical_name


_QUICK_ROLE_ALIASES = {
    "visitedlink": "link",
    "unvisitedlink": "link",
    "link": "link",
    "list": "list",
    "button": "button",
    "checkbox": "checkbox",
    "radiobutton": "radiobutton",
    "combobox": "combobox",
    "listitem": "listitem",
    "graphic": "graphic",
    "heading": "heading",
    "table": "table",
    "edit": "editabletext",
    "blockquote": "blockquote",
    "slider": "slider",
    "tab": "tab",
    "menuitem": "menuitem",
    "togglebutton": "togglebutton",
    "progressbar": "progressbar",
    "math": "math",
    "grouping": "grouping",
    "embeddedobject": "embeddedobject",
    "article": "article",
    "annotation": "annotation",
    "figure": "figure",
    "landmark": "landmark",
    "separator": "separator",
    "frame": "frame",
}

_QUICK_STATE_EVENTS = {
    "clickable": "state.clickable",
    "error": "state.invalidentry",
}

_CONTAINER_ROLES = frozenset({
    "", "unknown", "document", "window", "application", "pane", "rootpane", "internalframe",
})


def browse_cue(info, hint=None, root=None) -> str:
    """One meaningful role cue per virtual cursor move, else a caret cue.

    Quick-navigation knows the requested element kind even if NVDA does not
    expose that web node as a focusable object. For ordinary arrow navigation,
    inspect the node at the virtual caret rather than the OS keyboard focus.
    """
    if hint:
        name = canonical_name(hint)
        if name.startswith("heading") and name[7:].isdigit():
            return "role.heading"
        if name in _QUICK_STATE_EVENTS:
            return _QUICK_STATE_EVENTS[name]
        role = _QUICK_ROLE_ALIASES.get(name)
        if role:
            return "role." + role
    if info is not None:
        # A web link/button is often the focusable ancestor of a static-text
        # leaf. Prefer it; otherwise use the real node for headings and text.
        for attribute in ("focusableNVDAObjectAtStart", "NVDAObjectAtStart"):
            try:
                obj = getattr(info, attribute, None)
                if obj is None or obj is root:
                    continue
                role = canonical_name(getattr(obj, "role", None))
                if role not in _CONTAINER_ROLES:
                    return "role." + role
            except Exception:
                # Bad or stale web accessibility objects are common during
                # dynamic-page updates. Never break NVDA cursor navigation.
                continue
    return "nav.caret"
