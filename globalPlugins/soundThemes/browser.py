"""Reversible hooks for role-aware web Browse Mode cursor movements.

Unlike normal application focus, moving the virtual caret onto a web button,
link, checkbox or heading does not necessarily fire event_gainFocus.  Hook the
two NVDA cursor movement helpers, as the original navSounds add-on did, and
play one role cue for the element reached rather than a generic cursor click.
"""

from __future__ import annotations


class BrowseMonitor:
    def __init__(self, plugin):
        self.plugin = plugin
        self.patches = []

    def patch(self):
        import browseMode
        import cursorManager
        import textInfos

        def snapshot(instance):
            try:
                info = instance.makeTextInfo(textInfos.POSITION_CARET)
                return info.copy()
            except Exception:
                return None

        def moved(before, after):
            if before is None or after is None:
                return False
            try:
                return before.compareEndPoints(after, "startToStart") != 0
            except Exception:
                return False

        target = browseMode.BrowseModeTreeInterceptor
        original = getattr(target, "_quickNavScript", None)
        if original:
            quick_original = original
            def quick(instance, *args, **kwargs):
                # makeTextInfo can query a large remote/virtual document. Do
                # not pay that cost when web navigation audio is switched off.
                if (not self.plugin.setting("enabled") or
                        not self.plugin.setting("navigation")):
                    return quick_original(instance, *args, **kwargs)
                before = snapshot(instance)
                result = quick_original(instance, *args, **kwargs)
                after = snapshot(instance)
                if moved(before, after):
                    item = kwargs.get("itemType") or (args[1] if len(args) > 1 else None)
                    try:
                        self.plugin.browse_moved(after, item, getattr(instance, "rootNVDAObject", None))
                    except Exception:
                        pass  # Audio must never break NVDA keyboard navigation.
                return result
            setattr(target, "_quickNavScript", quick)
            self.patches.append((target, "_quickNavScript", original, quick))

        target = cursorManager.CursorManager
        original = getattr(target, "_caretMovementScriptHelper", None)
        if original:
            caret_original = original
            def caret(instance, *args, **kwargs):
                if (not self.plugin.setting("enabled") or
                        not self.plugin.setting("navigation") or
                        not self.plugin.setting("arrowNavSounds")):
                    return caret_original(instance, *args, **kwargs)
                before = snapshot(instance)
                result = caret_original(instance, *args, **kwargs)
                after = snapshot(instance)
                if moved(before, after):
                    if isinstance(instance, browseMode.BrowseModeTreeInterceptor):
                        # An arrow can move to a web button without changing
                        # keyboard focus. Use the object at the NEW caret.
                        try:
                            self.plugin.browse_moved(after, root=getattr(instance, "rootNVDAObject", None))
                        except Exception:
                            pass
                    else:
                        try:
                            self.plugin.play_event("nav.caret")
                        except Exception:
                            pass
                return result
            setattr(target, "_caretMovementScriptHelper", caret)
            self.patches.append((target, "_caretMovementScriptHelper", original, caret))

    def terminate(self):
        for owner, attribute, original, replacement in reversed(self.patches):
            if getattr(owner, attribute, None) is replacement:
                setattr(owner, attribute, original)
        self.patches.clear()
