# Original add-ons → Sound Themes for NVDA 0.17.0

## v0.17.0 regression review

- Compared archived installer Python sources for 0.13 → 0.14 → 0.15 → 0.16 against the current candidate. From 0.14 onward the playback engine did not change; recent settings/import regressions were not caused by a new audio library. Typing outside text fields came from the previous `onlyEditable=false` policy and the initial 0.16 build did not include the late repair. Event handlers for focus, browsing, typed characters, keypresses, caret and selected items remain present.
- Retained NVDA's `nvwave.WavePlayer` output device integration. Added dedicated input and navigation playback queues with a limit. Their diagnostic counters remain internal; the technical report button was removed from the user-facing settings. Because a queue can still overload and Windows may not send an event, zero audio omissions are not guaranteed.
- The attached general-purpose `skills.zip` does not supply an NVDA sound library or a required runtime module. See `DEPENDENCY_POLICY.md` for how to include future third-party modules safely.

## Post-release-candidate Windows log findings (unpublished)

- Confirmed user-reported Tools dialog error on NVDA 2026.2: `ModuleNotFoundError: No module named 'filecmp'` upon importing the editor's rollback helper. The actual dialog constructor was never reached. Local chunked WAV comparison avoids this missing standard-library module without touching NVDA input or sound events. The add-on's new error boundary remains helpful for other runtime failures.
- Desktop key clicks with Typing Sounds (not Keyboard Sounds) stemmed from `onlyEditable` being false on fresh and existing configurations, allowing `event_typedCharacter` outside editable controls. The new default and one-time migration set it true. Users can change it afterwards; dedicated Keyboard Sounds still plays physical keys globally if enabled.
- Added two independent regressions for these exact failures; now 76 offline tests pass. Need Windows NVDA re-test to certify actual Tools modal opening and the Desktop typing behavior.

## v0.16.0 UI and language audit

No underlying navigation, typing or keyboard event routing was altered. Sound manager Escape now maps to wx's standard Cancel dialog action; Escape from the keyboard capture field performs the editor's existing rollback, and Tab leaves that field so keyboard-only navigation remains available. The event list preserves source-compatible filenames. NVDA's standard gettext domain has a compiled Thai catalog; English is the fallback. HTML Help remains under `doc/<language>/readme.html` according to NVDA's add-on documentation conventions. These are source-level changes pending live Windows/NVDA confirmation.

## v0.15.0 Tools access, stable-GitHub update safeguards and duplicate-audio check

- Unlike v0.14, configuration is a standalone wx dialog under the official NVDA Tools menu; the standard NVDA Settings page is no longer registered. Native configuration keys are unchanged, so reinstalling does not reset users' selections. The menu binding is released in `terminate()` to avoid duplicate Tools entries after add-on reloads.
- Optional release checking follows the user-supplied LINE MR architecture, but restricts asset selection to an exact versioned `.nvda-addon` from this repository. Pure release validation tests reject untrusted asset hosts, drafts/prereleases, bad digest formatting and oversized files. Networking and download are on background workers. User confirmation and NVDA's own installer/restart flow are mandatory; checks can be disabled or skipped per version. Source must still be exercised on Windows NVDA.
- Local PowerShell release automation is excluded from both Git and `build_source.py`. GitHub Actions already supports publishing a tagged Release. Never imply that tagging alone bypasses Actions success or that the addon has joined the NVDA Add-on Store.
- Inspected all three common iPhone/VoiceOver Typing sample names with real hashes, bit depths, durations, and decoded waveform comparison: the sets are **not audio duplicates**, despite similar perceived style. Both are preserved as editable presets rather than deleting distinct recordings.

## v0.14.0 embedded editable packs, faster keyboard and ScreenReaderSounds/TalkBack completeness

- Presets in Navigation, Typing, and Keyboard are now directly editable, renameable, copyable, importable, exportable and removable, including presets shipped with the add-on. An `EmbeddedThemeStore` stores WAVs **only** at `globalPlugins/soundThemes/effects/{navigation,typing,keyboard}`. It never creates an extra `soundThemes/effects` sound directory at the NVDA configuration root. A read-only lookup for a previous external root allows **idempotent**, nondestructive migration into the embedded folder. NVDA's standard configuration stores playback mode and deleted-preset markers. Updating an installed add-on can overwrite custom WAVs in that add-on: users should export edits to ZIP before upgrades.
- Exactly **two** physical Keyboard Sounds playback modes: `separate` (one down WAV and optional distinct release WAV), and `combined` (one press WAV containing press and release; never replayed at keyup). Old `press` mode values are normalized to `combined` to preserve their keydown-only behavior. Raw-key handling remains nonblocking and never consumes Windows/NVDA keystrokes. Preview/playback output-device resolution is now one lookup per queued sound rather than per available voice. When Navigation is disabled, Browse Mode quick-navigation and caret hooks avoid all accessibility text-info work, preventing costly cursor inspection during Keyboard-only use.
- Replaced the nested event-group selector with a **single alphabetically sorted** list of short original event names (`checkbox`, `editabletext`, `typekey`, etc.); old filename aliases without `role.`/`key.` prefixes remain recognized. **Cancel**, Escape/window-close revert edits, while **Done** commits them; an editor session snapshots the original theme only upon its first change, not on opening the editor or pressing arrow keys.
- Read new genuine TalkBack and VoiceOver audio under `ScreenReaderSounds(1).zip`, including nested VoiceOver `objdata.zip`, using `import_screenreader_multitheme.py`. Packaged collection now contains **1,398 real PCM WAVs in 26 editable sound packs**, adding `navigation/talkback`, `typing/talkback` and one extra VoiceOver navigation cue. Where a canonical event is duplicated, original ScreenReaderSounds is preferred to NavigationSounds. No audio was fabricated.
- Compared the supplied original NavigationSounds source: it intercepts `event_gainFocus`, `event_mouseMove`, `event_typedCharacter` and Browse virtual cursor movement. Our add-on implements these plus additional NVDA object/state, foreground, speech, text and live-region callbacks (see main module), role/ancestor aware Browse traversal and physical keyboard down/up. These represent broader **implemented** coverage, **not proof** of all possible NVDA events. Browser focus behavior, keyboard latency, hardware keyup delivery and role/state mappings across Chrome/Firefox/Edge and other Windows apps **require live NVDA testing**.
- Updated regression suite to cover editable/removed installed presets, migrated legacy modes and audio, true Cancel restore, ScreenReaderSounds precedence and skipping Browse work with Navigation off. Test counts and packaging are recorded in `PROJECT_STATUS.md`.

## v0.13.0 keyboard press/release and original NavigationSounds re-audit

- Confirmed against official `nvaccess/nvda/source/keyboardHandler.py` and `inputCore.py` that `decide_handleRawKey` is a supported raw-key `Decider` called by **both** `internal_keyDownEvent` (`pressed=True`) and `internal_keyUpEvent` (`pressed=False`), with VK, scan code, extended and injected flags. Our handler returns `True`, discards injected input and never blocks OS/NVDA shortcuts; it only queues already-decoded audio. No second global hook.
- Physical-state transitions ignore repeated keydowns, duplicate generic/side-specific modifier aliases and keyups without prior press; regular Return and Numpad Enter are tracked separately. Keyboard presets support `press`, `separate`, and `combined` modes independent of Navigation/Typing. Combined WAVs can already contain both clicks and are never played again on keyup. Release fallback stays separate from the press fallback; user settings persist outside installed add-on and survive copying, renaming and ZIP roundtrip.
- Verified source filenames: Kliq uses decimal PC scan code `NN-down.wav` / `NN-up.wav`; the Bucklespring C implementation uses `NN-1.wav` for **press** and `NN-0.wav` for **release**. Bundled seven Kliq packs now carry mapped release recordings, and Bucklespring provides all 209 source recordings. Zero synthesized WAVs, with GPL v2 license reproduced for Bucklespring.
- Compared the provided **original NavigationSounds** `browser.py` and `__init__.py` again: it monkeypatches `_quickNavScript` and `_caretMovementScriptHelper`, checks role/state at virtual caret and calls `nextHandler` for ordinary events. Our v0.12 resolver is stronger where it restores monkeypatches safely, preserves the original method's return, handles focusable ancestors/quick hints, guards against exceptions and incorrect closure capture, and only plays cues on real cursor movement. The original additionally checks states before roles for caret movement; our current focus policy does this for ordinary controls with an exact-sound guard, preventing the original's missing-state masking problem. Do not copy unconditional state priority or its ineffective vision-module registration into working Navigation/Typing flows.
- Added seven independent regression tests covering phase semantics, auto-repeat/side modifiers, per-preset mode persistence and ZIP import/export, no release-to-press fallback, original Bucklespring phase convention, GUI wiring and an AST-executed real raw-key callback. Existing browser, typing, audio concurrency and Windows-key catalog regressions remain active; **56/56 offline tests passed** before distribution build. Real NVDA Windows keyup delivery and voice overlap still require hands-on user acceptance testing.

## v0.12.0 web Browse Mode event-completeness audit

- Confirmed with the original navSounds code, sound packs and upstream `nvaccess/nvda` source that browser virtual caret movement does not necessarily generate an NVDA keyboard `event_gainFocus`. **Both** built-in Navigation packs already contain real button, link, heading, checkbox, radio button and menu-item WAVs; no additional recordings needed to be invented.
- Identified two concrete defects: the `vision.visionHandlerExtensionPoints` import targets a module declaring a dataclass, not a `post_browseModeMove` action instance; and two monkeypatch closures used the same mutable `original` reference, leading `_quickNavScript` to call the caret helper with an incompatible signature after `patch()` finished. Corrected both by consistently installing reversible cursor hooks with independently captured original methods.
- The new `browse_events.py` resolves semantic roles for quick-navigation item types and the actual virtual-caret object. Quick navigation handles B/K/H and further NVDA target classes; arrow movement prefers the current link/button ancestor over static text. One role cue is emitted per confirmed cursor movement, with a genuine `nav.caret` fallback when no accessible role is available, rather than layering several unrelated clicks. No mutation of original WAVs or gesture consumption.
- Added **three new browser behavior regression tests** (role resolution, hook integration/restoration, and actual built-in sound presence), raising the offline suite to **49 tests**. Must still validate real Windows/NVDA role delivery in Chrome/Firefox/Edge and sound interplay with third-party add-ons.

## v0.11.0 typing completeness and removable presets

- Audited all **13 bundled typing packs** for Enter/Space/Backspace. Every pack contains genuine `key.character` audio, but **11 lack a distinct Enter WAV, 4 lack a distinct Space WAV, and 5 lack a distinct Backspace WAV**. The missing dedicated samples were **not supplied**; they have not been fabricated or reported as independently imported.
- Raw-key listener triggers `key.enter`, `key.space`, `key.backspace` (also Delete) on the first physical press **only in focused editable controls** while Typing Sounds is active. Matching later NVDA `event_typedCharacter` callbacks within 500 ms are consumed once. A dedicated WAV wins; a missing event falls back to a genuine `key.character` WAV in the selected pack. Both `ThemeStore` lookups and engine playback use identical candidate event rules.
- Removed the obsolete **Import old sounds folder** UI button. Every built-in preset can now be removed from the list; per-category JSON tombstones are stored in writable NVDA config so add-on upgrades do not silently restore deleted selections. Restoration is explicit via the manager. Deleting personal themes removes their folder. Zero themes in a category is valid; no forced empty default is created. Built-in editing and renaming remain read-only; copy to a personal theme to edit.
- Expanded offline regressions from 42 to **46 tests**. Live NVDA/Windows keyboard-hook behavior and wx accessibility remain pending acceptance tests.

## v0.10.0 speech-pause/Shift audit and event accessibility

- **Confirmed cause from user test and source:** after deleting the `Speech feedback paused` WAV, the extra Shift sound stopped. NVDA's `post_speechPaused` callback was unconditionally playing `system.paused_feedback` when speech was paused; this is a *System*, not Navigation, event, so toggling Navigation was ineffective. Physical modifier deduplication from 0.9.0 addressed a different duplication path.
- New `pauseFeedback` is false by default for existing and new installs, independent of System and Keyboard modes. With it enabled, skip Shift-driven speech-pause events while Shift is held or for 350 ms after its last raw-key report. Physical Shift WAV is unaffected. The legacy pause event remains a configurable assignment and preview. Windows NVDA timing is not yet validated.
- New `catalog.event_description` provides a separate human explanation for every catalog event (including all runtime NVDA roles/states and 255+ physical key identifiers). Specific examples include Explorer file list vs folder tree, browser tabs, document objects and Windows dialogs. Unknown/unsupported legacy events are identified as such. The wx editor has an accessible read-only description field and an optional delayed, latest-only speech announcement on selection; event list labels are unchanged for first-letter search.

## v0.9.0 physical Shift and missing original navigation/typing sounds

- The NVDA raw-key hook can encounter generic Windows modifier VK aliases (Shift `0x10`, Control `0x11`, Alt `0x12`) as well as left/right virtual-key codes (`0xA0`–`0xA5`). The pressed-key tracker now maps generic Shift with scan code `0x2A` / `0x36` onto physical left/right Shift, and maps generic Control/Alt using the Windows extended-key bit. Thus duplicate generic + sided keydown reports no longer play two samples for one held physical key, while two physically distinct Shift keys remain distinct. These nonblocking callbacks still never consume NVDA keyboard input.
- Validated all **86 navigation and 61 typing PCM WAVs** in the user's `upload/effects.zip`. Imported a standalone `navigation/default` pack of 85 distinct cues (one duplicate editable-text alias), and merged **59 previously missing NVDA event recordings** into active VoiceOver without overwriting the original SRS assignments. Fixed legacy typos (table column header/row, invisible, expanded) and separated role, state, caret and completion events.
- Added eleven independent typing packs; extended existing Classic Typewriter with its original bell. Within each folder identical real sound data for the same canonical event is stored only once. The project now includes **706 real WAVs** in 23 built-in packs, all below `globalPlugins/soundThemes/effects/`, without a `theme.json` or synthesized-audio generator.
- **39/39 independent Python tests pass**, including Shift alias and new audio mapping checks. Actual Windows/NVDA interaction and possible sounds generated by other running add-ons/Windows accessibility options still require live diagnosis; the additional Shift sound is not claimed to be proven eliminated on a user's computer until tested there.

## v0.8.0 keyboard-first preview audit

- All three settings theme selectors and all three manager theme lists audition a real in-pack sample on **user-initiated selection change**, without activating the pack or blocking wx to decode the WAV. The event editor's list also auditions the selected event if its WAV exists, without an unwanted message box for missing audio.
- Native first-letter search now works because manager names are `Cherry`, `KAT`, etc., not `Built-in: Cherry`. Event-list names omit prefixes `Role:`/`State:` and the ` (assigned)` suffix; keyboard letter/digit labels begin directly with the character. Category separation and assignment information remain available outside list item names.
- `AudioEngine` adds one latest-only decode worker with a small preview cache and a generation guard. This prevents an old preview that is still decoding from being queued after the user has moved to a newer item; it reuses the existing twelve-voice bounded playback engine.
- All 510 original WAV assets are unchanged. Offline tests verify representative pack selection, first-letter labels, and stale-preview cancellation; live Windows/NVDA UI acceptance tests remain necessary.

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
