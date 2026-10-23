# Original add-ons → Sound Themes for NVDA 0.7.0

## v0.7.0 polyphonic playback and single packaged sound root

- `audio.py` now runs up to twelve independent, reusable NVDA `WavePlayer` streams, each with its own worker. A long cue cannot serialize other navigation/typing cues and playing a new sound does not call `stop()` on streams already sounding. Each worker calls NVDA's `idle()` to wait for its own completion; no per-keystroke creation of extra threads.
- Incoming event callbacks remain nonblocking. Playback work and its short pending queue are bounded; if every voice is occupied, obsolete *waiting* cues are replaced with recent ones. Saturation may omit individual clicks rather than allow unlimited delayed playback.
- All 510 real built-in WAVs were moved under `globalPlugins/soundThemes/effects/{navigation,typing,keyboard}`, alongside the plugin. User-created themes remain in the separate writable NVDA user-config `soundThemes/effects` location so they survive updates. Removed the obsolete synthetic sound generator from the **source** scripts; no generated sound assets are shipped.
- Authorship and homepage metadata now identify Nuttawat Seecham and the new public GitHub repository. An official-GitHub-actions-only workflow builds installers and publishes a tagged Release.
- Offline concurrent/long-audio and saturated-queue tests added; Windows NVDA actual playback must still be tested.

## v0.6.0 audio fidelity and latency audit

- Inspected the actual user-provided `Sounds.zip`: **881 WAV files** across seven Kliq switch sets plus eight standalone effects. Importing only the recorded key-down samples preserves seven genuinely distinct sets and omits all unused key-up samples; 447 canonical keyboard WAVs are installed (including seven fixed genuine in-pack fallback sounds). The supplied original ScreenReaderSounds/navSounds recordings remain available.
- Explorer `State.SELECTED` previously won before `Role.LISTITEM` but had no assigned `state.selected` sample. A focused selected file therefore produced **silence despite `role.listitem.wav` being present**. Role selection now plays that actual item sound, and item selection events can provide the same cue without relying on an additional focus event.
- Reduced playback lag: a 12-sample pending queue could hold old item cues after focus had moved; the prior code already called `stop()` before every `feed()`. Queue now keeps only the latest pending sound, and the worker discards superseded items; rapid navigation does not replay a backlog. Raw keyboard cues no longer wait for wx event-loop dispatch.
- Reduced spurious sounds by removing the fake tree-collapse-on-focus transition, suppressing repeated identical focus/selection cues within 75 ms, prioritizing one state-change cue over four, and restricting caret sounds to recent navigation presses.
- Offline tests do not establish that every NVDA 2026 focus/object event is emitted by every Windows application. Particularly secured desktops and hardware Fn buttons still require live verification.

## New v0.5.0 integration notes

- ScreenReaderSounds is now available as an **audio-bearing 17 MB ZIP**; 54 original event assignments were imported, including WAVs from nested `objdata.zip`, three decoded OGG recordings and three dedicated keyboard cues. The active project contains 62 genuine WAVs total. Statements in the following historical v0.4.0 audit about absent ScreenReaderSounds audio are superseded.
- Added independent **Keyboard Sounds**, default OFF, mutually exclusive with the default-ON Navigation and Typing modes. Raw key-down audio is exclusively a Keyboard Sounds feature: Tab, Home, End, PgUp/PgDn and arrows no longer play a key cue merely because Navigation is enabled.
- Each key gets one `keyboard.keyname.wav`, no random choice and no other-pack borrowing; mappings include all 255 defined/unknown Windows VK values and extension names for Fn/brightness. Actual hardware keys are limited by Windows/NVDA raw key delivery.
- Settings now has **one** Manage Sound Themes dialog (Navigation/Typing/Keyboard tabs) and **one** Open Sound Folders action. Editor captures/chooses/previews a pressed key when its capture field is focused.
- Speech pause now uses NVDA's documented `post_speechPaused` extension point. Original long-click, tutorial and volume-beep cues remain assignable but lack verified automatic NVDA 2026 triggers. Unprovided TalkBack audio and Mechvibes individual-key packs remain missing.

## Historical v0.4.0 source-only review

Previously reviewed code-only inputs `upload/navSounds.zip` and the earlier SRS source ZIP. This old limitation was resolved for the supplied ScreenReaderSounds recordings in v0.5.0. The review does **not** substitute for live NVDA 2026 testing.

## navSounds capabilities

| Source behavior | Integrated implementation / qualification |
|---|---|
| Role-aware focus and state cues | Dynamic runtime `Role` and `State` enumeration in `catalog.py`, with `event_gainFocus`, `event_stateChange` and optional user-supplied fallback WAVs. |
| Browse-mode keyboard navigation | NVDA browse-mode extension listener or reversible `BrowseMonitor` fallback. |
| Character/space/backspace/protected typing | `event_typedCharacter`; optionally only editable fields; random character variations taken only from active typing pack. |
| Mouse hover, ignore noisy surfaces and hover delay | `event_mouseMove` plus configurable delayed playback; `mouse` toggle defaults off. |
| Speech role/state suppression | Reversible `getPropertiesSpeech` wrapper; retains speech when no exact WAV is assigned. |
| Folder-based theme browsing and switching | `folderpacks.py`; native WAV names, separate navigation/typing themes and settings, no theme manifest. |
| Volume and wave output | `audio.py`, PCM WAV cache and NVDA `nvwave` with current output-device callback; no BASS DLL. |
| NVDA+Alt+N | Keeps navigation toggle; repeated gesture toggles typing; additional global toggle and navigation pack cycling. |

## ScreenReaderSounds: all 21 named WAV cues

Imports map case-insensitive old filenames to the following event IDs. Synonyms with the same meaning are intentionally unified.

| Original filename | New event | When emitted |
|---|---|---|
| `Tab.wav` | `key.tab` | Tab navigation |
| `ShiftTab.wav` | `key.shift_tab` | Shift+Tab navigation |
| `clicked.wav` | `nav.activate` | Activating controls |
| `media.wav` | `system.media` | Media key; old pack exposed filename but lacked active playback path |
| `scroll.wav` | `nav.scroll` | Scroll/page navigation |
| `typekey.wav` | `key.character` | Normal text, random variation |
| `typekeyspace.wav` | `key.space` | Space |
| `typekeypr.wav` | `key.protected` | Password/protected field |
| `typekeyremove.wav` | `key.backspace` | Backspace/Delete |
| `closed.wav` | `nav.close` | Escape/leave Explorer context |
| `opened.wav` | `nav.open` | Open/enter Explorer context |
| `notext.wav` | `nav.empty` | Unnamed focus |
| `collapsed.wav` | `nav.collapse` | Collapsed |
| `expanded.wav` | `nav.expand` | Expanded |
| `eclose.wav` | `nav.edit_exit` | Left edit/document context |
| `delete.wav` | `key.backspace` | Same event as `typekeyremove.wav` |
| `lock.wav` | `system.lock` | Session lock transition |
| `lockscreen.wav` | `system.lockscreen` | Delayed follow-up lock-screen cue |
| `unlockscreen.wav` | `system.unlock` | Session unlock |
| `error.wav` | `key.invalid` | Invalid navigation in list/tree |
| `end.wav` | `key.home_end` | Home/End key |

Role-named WAVs map to `role.*`; state-named WAVs map to `state.*`. Further integrated effects cover focus, caret, selection, notifications, alerts, document/live-region/object changes, foreground/app changes, browse mode, secure-desktop transitions and more. The editable event list is populated from current NVDA roles/states, but every application does **not** necessarily deliver all of these callbacks.

## `k` library integration decision

The bundled `k` module in ScreenReaderSounds is a fork of a `keyboard`-style library using its own Windows low-level global hook; the old add-on used `k.is_pressed()` primarily for arrow keys and Tab/Shift+Tab context. `keyboard_state.py` **adapts that useful pressed-key tracking behavior** and registers to NVDA's existing `inputCore.decide_handleRawKey` callback. We intentionally **do not bundle the whole original `k` library**: an extra low-level hook, key injection and its unused/deprecated mouse API would duplicate NVDA's native facilities. This is a deliberate functional merge, not literal reuse of the old dependency; Windows runtime confirmation remains necessary.

Original ScreenReaderSounds had commented-out secure-object detection. Here `post_sessionLockStateChanged` handles lock/unlock, with an extra listener for `post_secureDesktopStateChange` where present. Protected desktops are still subject to NVDA's system configuration and security policies. Mouse behavior uses navSounds' NVDA mouse events instead of `k.mouse`.

## File layout and backwards compatibility

```text
globalPlugins/soundThemes/effects/
  navigation/voiceover/*.wav
  typing/classic-typewriter/*.wav
```

New themes contain **WAVs only**, with canonical names such as `role.button.wav`, `state.expanded.wav`, `key.tab.wav`, `system.lock.wav`, `system.secure_enter.wav`, and variations `key.character__1.wav`. The 15 actual navigation WAVs and six typing variations in v0.4.0 do **not** cover every assignable event; other sounds require original audio to be supplied by the user. An arbitrary unknown WAV inside the active **typing** pack becomes an additional character typing variation, never sampling another pack. Direct WAV-only theme ZIP export; WAV-only and older manifest import. Older personal themes are retained or backed up during conversion.

The original navSounds lowercase `tab.wav` is a **tab control role** (`role.tab`), but ScreenReaderSounds' capitalized `Tab.wav` is a **Tab keystroke** (`key.tab`). The source-aware audio importer keeps them separate. When a complete ScreenReaderSounds archive is supplied, it merges same-event sounds with ScreenReaderSounds priority rather than losing unique role/navigation events. See `SOUND_SOURCES.md`.

## Remaining validation

Python static/unit tests are not a replacement for a running Windows NVDA 2026. Test mouse timing, raw key decider signatures, actual playback/secure desktop, all dialog labels and keyboard operation, old-theme migration and interactions with third-party add-ons. No claim of 100% Windows runtime coverage is made without this step.
