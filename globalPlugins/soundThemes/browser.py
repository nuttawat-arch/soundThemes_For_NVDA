"""Carefully reversible fallback for browse/caret moves in older NVDA builds."""

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

        target = browseMode.BrowseModeTreeInterceptor
        original = getattr(target, "_quickNavScript", None)
        if original:
            def quick(instance, *args, **kwargs):
                before = snapshot(instance)
                result = original(instance, *args, **kwargs)
                after = snapshot(instance)
                if before is not None and after is not None:
                    try:
                        if before.compareEndPoints(after, "startToStart") != 0:
                            self.plugin.play_event("nav.quick")
                            item = kwargs.get("itemType") or (args[1] if len(args) > 1 else None)
                            if item:
                                self.plugin.play_event(f"role.{str(item).lower().replace('_', '')}")
                        else:
                            self.plugin.play_event("key.invalid")
                    except Exception:
                        pass
                return result
            setattr(target, "_quickNavScript", quick)
            self.patches.append((target, "_quickNavScript", original, quick))

        target = cursorManager.CursorManager
        original = getattr(target, "_caretMovementScriptHelper", None)
        if original:
            def caret(instance, *args, **kwargs):
                before = snapshot(instance)
                result = original(instance, *args, **kwargs)
                after = snapshot(instance)
                if before is not None and after is not None:
                    try:
                        if before.compareEndPoints(after, "startToStart") != 0:
                            if self.plugin.setting("arrowNavSounds"):
                                self.plugin.play_event("nav.caret")
                        elif self.plugin.setting("arrowNavSounds"):
                            self.plugin.play_event("key.boundary")
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
