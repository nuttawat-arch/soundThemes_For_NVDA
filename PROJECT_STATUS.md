# Sound Themes for NVDA — Project status v0.17.0 (2026-10-24)

## Current: v0.17.0 candidate, NOT released

- User's PowerShell output verifies `main` commit `9b2dc28` and `v0.16.0` tag were pushed to `nuttawat-arch/soundThemes_For_NVDA`. The local Windows release process then ran **67 tests** and built a 32,134,097-byte installer. Therefore **the released v0.16.0 is not identical to the later 76-test, unpublished local hotfix archive** documented below. Do not overwrite or reuse `v0.16.0`.
- The earlier NVDA 2026.2 log confirmed `ModuleNotFoundError: No module named 'filecmp'` while opening Tools → Sound Themes settings. The portable, chunked-WAV comparison from the unpublished hotfix is preserved here; one-time correction of desktop Typing Sounds (`onlyEditable`) is also preserved. The first published v0.16.0 does not contain those two late fixes, according to the user's 67-test release transcript.
- Audited v0.13–0.16 installer archives. The sound engine's queue/playback structure is unchanged from v0.14 through v0.16; the only v0.13→v0.14 audio change was caching the selected output-device lookup per cue. v0.14 changed the location of editable packs and eliminated a short raw keyboard debounce; v0.15 moved the settings to Tools; v0.16 introduced GUI cleanup. There is no evidence the basic 3-mode event dispatch was removed, but full compatibility cannot be guaranteed without Windows NVDA testing.
- New in this candidate: separate bounded FIFO for text-input and physical keyboard sounds, serviced before the latest-only Navigation/other queue. Busy navigation events cannot evict all keyboard feedback. When both queues are saturated, events can still be skipped for low-latency playback. Added a user-facing Tools → Settings → **Sound playback report...** showing both queue depths and skipped-counts; no sample bytes or event assignments changed.
- Dependency decision: retain NVDA's built-in `nvwave.WavePlayer` (native WASAPI) rather than adding a new BASS/Sound_lib runtime and potentially introducing DLL/ABI, audio-device and license regressions. See `DEPENDENCY_POLICY.md`, based on the official NVDA 2026.2 developer guide. BASS's licensing depends on whether the resulting product earns revenue.
- **78 offline tests pass after the new queue, worker-priority and diagnostics changes.** Thai translations compiled successfully. Both 0.17 archives were built and passed full ZIP-integrity checks, with **1,398 WAVs identical byte-for-byte to the preceding 0.16 local candidate**. The installer includes `doc/en/readme.html`, `doc/th/readme.html` and `locale/th/LC_MESSAGES/nvda.mo`; neither package contains the private `release.ps1`. Still pending: hands-on Windows NVDA 2026.2 testing; no GitHub push/tag/release/Store submission performed for v0.17.

## Historic v0.16.0 development record (some notes below predate the user's subsequent release)

## Completed in v0.16.0

- **Confirmed failure from user's pre-hotfix NVDA 2026.2 log at 21:34:30:** Tools → Sound Themes settings failed during `settings.py` import because `theme_edit_session.py` imported Python's `filecmp`, which is absent in NVDA's bundled interpreter (`ModuleNotFoundError: No module named 'filecmp'`). Replaced `filecmp` with a local, chunked byte-by-byte comparison and preserved lazy snapshot/No-default discard confirmation. Separately, Typing Sounds on non-editable Desktop objects came from `onlyEditable` being false by default while `event_typedCharacter` is fired for quick-search characters. New installations default to typing sounds in editable controls only; existing profiles get a one-time, opt-out migration to the same behavior. Keyboard Sounds continues to intentionally emit raw physical key sounds everywhere when explicitly enabled. Added missing-module import regression, identical-length WAV comparison and Desktop/editor typing policy tests. **76/76 offline tests passed**; requires user validation on their actual NVDA before claiming fully fixed. No GitHub update.
- **Unpublished Tools-dialog investigation:** User reports that activating Tools → Sound Themes settings does not open a window on actual NVDA. A source-level review and new dynamic headless wx constructor checks exercised Settings, Theme Manager and all three editors without errors; additional tests simulate the menu's successful and failed modal lifecycle and safe Yes/No Escape behavior. The prior menu callback had no error boundary, making real NVDA/wx exceptions silent. `_show_settings` now logs full exception details, displays a translated user-facing failure message, safely destroys partial windows and clears its busy flag; `_on_tools_settings` also catches scheduling failures. Added Thai translation and bilingual log-retrieval troubleshooting. **All 74/74 offline regression tests now pass. The underlying Windows-only failure remains unconfirmed pending the user's NVDA log and a real NVDA test; do not call this issue fixed yet.** No GitHub update or tag.
- **Post-build follow-up, not published:** Added a safe discard-confirmation flow in the sound editor for Escape, Cancel and title-bar Close. When any WAV differs from the edit-session snapshot, the dialog asks whether to discard; **No is the default and preserves all current changes with the editor open**, while **Yes** rolls back the complete session and exits. If no sound file changed, closing requires no confirmation. The editor disables wx's automatic Escape dismissal so the warning cannot be bypassed. Added Thai translations, English/Thai Help explanations and change detection coverage. **All 69/69 offline tests still pass.** No GitHub push or tag has been made; this correction remains a local, unpublished 0.16.0 candidate.
- Reworked end-user text in Sound Settings, the three-pack manager and event editor to emphasize what each option does rather than WAV layers, NVDA role/state internals, or legacy implementation labels. Preserved original short event filenames for importing historic packs and alphabetic list navigation.
- Fixed the manager's Esc behavior: Close now uses the standard `wx.ID_CANCEL`, and `SetEscapeId` is assigned in the manager, standalone Settings and event editor. Esc in the keyboard-capture field explicitly cancels the editor with its existing safe rollback. Tab now navigates to the next control instead of becoming trapped in key capture; users can assign the Tab key by selecting its item from the event list.
- Added native Thai gettext translations in `locale/th/LC_MESSAGES/nvda.po` and compiled `nvda.mo`, and localized Thai manifest metadata; English remains the built-in source-language fallback. Included `locale` in the actual installer build, not merely the source ZIP. The localized status, dialogs, Tools item, navigation/typing/keyboard tabs and updater messages use NVDA's add-on translation mechanism.
- Replaced the old long release-history HTML in `doc/en/readme.html` and `doc/th/readme.html` with parallel, screen-reader-friendly current user manuals (contents links, modes, pack manager, editor, keyboard, hotkeys, update backups and troubleshooting). `docFileName=readme.html` is unchanged so the Add-on Store/installed add-on Help action resolves the proper language folder automatically.
- No WAV files or audio event logic were changed. This update is packaged as 0.16.0 and **not pushed** to GitHub. Offline tests validate source wiring and translations, not actual Windows NVDA runtime behavior; live keyboard focus, localized menu and Help selection remain to verify.

## v0.16.0 validation and outstanding work

- **69/69 offline unit tests passed** (including the new Esc/Thai Help checks). Thai `nvda.po` compiled successfully with `msgfmt --check-format --check-header`. Both 0.16.0 ZIP archives passed integrity checks. The installer contains **1,398 original WAVs**, `doc/en/readme.html`, `doc/th/readme.html`, and Thai `nvda.mo`; the source ZIP excludes the private `release.ps1`. No GitHub release has been created.
- Pending hands-on NVDA Windows testing: Escape handling from every manager/editor child control, rollback after Escape, language changes to Thai/English, localized Help in Add-on Store and update UI. Always back up any edited in-add-on WAV packs before installing an update.

## Completed in v0.15.0

- Moved the **entire Sound Themes configuration UI** to a standalone, screen-reader-accessible dialog at **NVDA menu → Tools → Sound Themes settings...**. Removed the `NVDASettingsDialog.categoryClasses` registration; the Tools menu item is unbound and removed when the global plugin terminates. Existing native NVDA config values and the Navigation/Typing/Keyboard managers remain intact; standalone window offers OK/Cancel.
- Added a small GitHub Releases update client in `release_info.py` / `updater.py`: after 15 seconds an optional background check queries the stable release feed, identifies the exact versioned `SoundThemesForNVDA-VERSION.nvda-addon` asset, rejects unrelated hosts, suspicious filenames, prereleases and oversized downloads, and checks SHA-256 when GitHub supplies a digest. **Manual** Check for updates now and startup-check enable/disable are in the Tools dialog; update offers **Update now / Later / Skip this version**. Downloading runs off the NVDA/wx UI thread; actual installation uses `gui.addonGui.handleRemoteAddonInstall` with NVDA's standard confirmation/restart. No NVDA Add-on Store involvement.
- Added local-only Windows PowerShell `release.ps1`: validates existing `main`/official `origin` and tags, runs tests, updates the manifest/document headings, builds both release archives, validates that the private script is not inside either archive, commits/pushes `main` and creates/pushes a fresh version tag. GitHub Actions then creates the downloadable Release. `release.ps1` is **explicitly Git-ignored and excluded from `build_source.py`**; distribute it separately to the maintainer and keep it in the project root locally, never in Git.
- Audited suspected typing-sound overlap: `iphone-keyboard` has 16-bit/44.1kHz samples while `voiceover` uses 24-bit/44.1kHz samples. All three common event WAVs have different source hashes; decoded character waveforms show almost zero correlation. Similar timbre is not identical recordings. Kept both independently editable and removable to preserve source material.
- Extended NVDA-independent regression suite with release asset security/version tests, Tools-menu wiring, script exclusion, and audio nonidentity checks. **67/67 offline tests passed**; compilation of all Python sources succeeded. The 0.15.0 installer and full source ZIP both passed ZIP integrity checks. The installer reports `0.15.0`, includes the two update modules and all **1,398 original WAVs**; neither archive contains the private `release.ps1`, which is delivered separately.

## v0.15.0 verification and remaining acceptance

- **Pending Windows NVDA 2026 testing:** focus and keyboard operation of the Tools dialog, exact startup/update dialogs, the add-on installer/restart handoff, and PowerShell 5.1/Git authentication with `release.ps1`. Offline tests establish source behavior, not live Windows UI interaction.
- **Preserve customized sound packs:** because writable WAVs remain inside the installed add-on, export any changed presets before accepting a GitHub update. An update can replace their files. The update dialog explicitly warns about this. The latest confirmed remote tag from the user remains v0.12.0; **v0.15.0 has not been pushed**.

## Completed in v0.14.0

- Removed creation/use of a separate editable audio root under the NVDA user-config directory. Every Navigation, Typing, and Keyboard pack is managed directly under the installed add-on's `globalPlugins/soundThemes/effects` tree. All packs—including shipped packs—can now be edited, renamed, deleted, imported and exported. Existing external custom packs are copied **nondestructively** once to the installed tree when found; old folders are not recreated. Per-pack deletion markers, import map and keyboard mode preferences are stored in standard NVDA config.
- Reduced per-keyboard-preset mode selector to **two modes**, `separate` (two actual press/release WAV layers) or `combined` (one WAV with both sounds played on initial press only). Historical `press` settings remain playable as `combined`; no missing-keyup repeat is introduced. Auto-repeat and modifier deduplication remain active.
- Reduced Browse Mode's unnecessary accessibility cursor inspection when Navigation Sounds are off, especially relevant during physical Keyboard Sounds playback. Optimized per-cue audio output-device selection in the background worker without inserting delays into the raw-key handler.
- Replaced editor event categories with **one flat alphabetical list** using short original event labels and legacy bare-WAV filename compatibility. Added **Cancel** (and window-close) to revert any change made during an editor session, with a lazy local snapshot; **Done** commits changes.
- Imported genuine TalkBack and VoiceOver navigation/typing WAVs from new supplied `ScreenReaderSounds(1).zip`, preferring original ScreenReaderSounds event recordings on overlap. Now **1,398 genuine WAVs in 26 directly editable presets**. Added a deterministic `scripts/import_screenreader_multitheme.py` importer.
- Reviewed original NavigationSounds focus/mouse/typed-character and Browse Mode logic against implemented NVDA handlers and tests; broader callback coverage is documented, but **real Windows NVDA compatibility remains unverified**. **62/62 independent offline tests passed** on 2026-10-24, including legacy bare filename precedence, all-preset management, reversible editor cancel, migration and new SoundReaderSounds pack priority. Installer/source archives are validated separately below.

## Outstanding Windows validation and important update caveat

- Release packaging verified: `SoundThemesForNVDA-0.14.0.nvda-addon` (about 31.8 MB) and `SoundThemesForNVDA-source-0.14.0.zip` (about 32 MB) both passed ZIP integrity checks. The installer declares `version = "0.14.0"` and contains exactly **1,398 WAV recordings**. The source ZIP is a full replacement snapshot, not a commit; GitHub push/tag is still the user's choice.

- **Custom WAV edits inside the installed add-on may be overwritten when NVDA replaces that add-on during an update.** Export changed sound packs to ZIP before upgrading, then reimport as necessary. The deliberate removal of the separate persistent sound directory creates this trade-off; installed presets are not protected read-only defaults.
- Run hands-on NVDA/Windows trials for first press/release on each modifier side, NumPad, application switching latency, Browser Browse Mode/quick-navigation, and screen-reader audio in Chrome, Firefox, Edge and desktop apps. Offline mocks cannot establish all live key/role events. The user-reported 0.13.0 source was not published; the user's most recently confirmed GitHub push/tag was **v0.12.0**. The v0.14.0 work in this workspace is **not automatically pushed to GitHub**.

## Completed in v0.13.0

- Verified official NVDA `inputCore.decide_handleRawKey` is called from both `internal_keyDownEvent` and `internal_keyUpEvent` with `pressed=True/False`. Implemented first press **and** first release tracking on the existing NVDA event hook, with auto-repeat suppression and generic-versus-sided Shift/Ctrl/Alt deduplication, distinct extended Numpad Enter, numpad navigation keys and injected-key rejection. The handler continues returning `True` without blocking Windows or NVDA shortcuts, and audio dispatch uses the existing bounded worker/voice pool.
- Implemented **three independent playback modes per keyboard preset**: `press` (one press WAV), `separate` (press + dedicated keyup WAV), and `combined` (one already-joined WAV on keydown only). `keyboard.a__release.wav` maps to a distinct `keyboard.a.release` event; missing release recordings never accidentally reuse press audio. Each mode is stored outside the installed plugin in NVDA user config. Previously selected builtin/custom presets and personal audio remain intact; create/copy/rename/delete, ZIP export and import retain per-preset mode where applicable.
- Added mode selection to the accessible Keyboard Sounds manager and individual Replace/Preview/Remove release WAV controls to the keyboard event editor. Left Navigation and Typing controls, event routing and modes otherwise unchanged.
- Imported real original Kliq `*-up.wav` keyup audio into all seven existing keyboard packs. Added `keyboard/bucklespring` as an eighth keyboard switch preset with **all 209 original `NN-1.wav` (keydown) and `NN-0.wav` (keyup) samples** from the supplied archive. Original Bucklespring copyright and GNU GPL v2 license documented and supplied in `doc/BUCKLESPRING_LICENSE.txt`. No audio synthesized/concatenated; total installed 1,355 genuine WAVs across 24 theme folders.
- Rechecked original NavigationSounds movement hooks, state/role priority, navigation focus event handling and differences from our protected v0.12 browser cursor hooks. Findings are recorded in `FEATURE_AUDIT.md`, with no risky replacement of functional Navigation or Typing behavior.

## v0.13.0 verification and remaining Windows acceptance

- **56/56 offline Python tests passed**, including seven new keyboard release/mode regression tests and a direct simulation of NVDA's real raw-key callback. Created `SoundThemesForNVDA-0.13.0.nvda-addon` and `SoundThemesForNVDA-source-0.13.0.zip`; both passed ZIP integrity checks, installer `manifest.ini` declares `0.13.0` and its contents include **1,355 real WAVs**. Pending: keyboard GUI/real Windows NVDA audio testing across Ctrl/Alt/Shift/Win/Caps Lock, numpad, auto-repeat, secure desktop and switching applications. Verify that selected user presets and their removal records survive installing over 0.12.0. GitHub `v0.12.0` push succeeded at commit `17eec09`; **v0.13.0 has not been pushed/tagged**.

## Completed in v0.12.0

- Re-audited the real original `upload/navSounds.zip`, supplied `upload/ScreenReaderSounds.zip`, the installed `navigation/default` and `navigation/voiceover` WAV folders, and current NVDA upstream Browse Mode/cursor APIs. Both installed navigation packs already contain real `role.button`, `role.link`, `role.heading`, `role.checkbox`, `role.radiobutton` and `role.menuitem` recordings. The missing browser feedback was predominantly **event routing**, not missing audio.
- Fixed a genuine closure-variable capture bug in `BrowseMonitor.patch`: the `_quickNavScript` wrapper inadvertently invoked `_caretMovementScriptHelper` because both wrappers captured the same reassigned `original` variable. Single-letter browser Quick Navigation could thus receive the wrong call signature and fail. Each wrapper now stores the correct original callable and restores it on shutdown.
- Removed an ineffective registration against `visionHandlerExtensionPoints.post_browseModeMove`: the imported name is the **module containing the extension-point class**, not an instantiated action. Instead, installed reversible browse/caret movement hooks consistently, regardless of whether the vision module imports. After an actual virtual-caret move, they resolve a **single role-specific** sound using quick-navigation item types or the new virtual-caret object's role; focusable web ancestors (such as links wrapping text) win over static text leaves. A generic caret cue is used only if the role cannot be determined. No event is played when navigation fails to move, and normal NVDA keyboard input passes through.
- Expanded support for NVDA Quick Navigation targets including buttons, links, headings by level, menu items, toggles, lists, checkboxes, radio buttons, tabs, sliders, clickables and invalid entries. Added fully NVDA-independent regression tests for role resolution, quick navigation, arrow movement, no movement, original method preservation, and presence of real browser role WAVs in both source packs. Updated the English and Thai contextual role descriptions.

## v0.12.0 verification and pending Windows acceptance

- **49/49 Python regression tests passed**. Built `SoundThemesForNVDA-0.12.0.nvda-addon` and `SoundThemesForNVDA-source-0.12.0.zip`; both passed ZIP integrity checks. Installer manifest reports 0.12.0 and contains the new `browse_events.py` plus all 706 WAV recordings. Still need live NVDA on Windows (Chrome, Firefox, Edge) to confirm Browse Mode role audio using B/K/H and arrows in actual virtual buffers, ensure audio cues never double, and verify add-on interactions with other global plugins. No new WAVs required.

## Completed in v0.11.0

- Inspected all **13 bundled typing packs** plus the source `effects.zip`. Every typing pack has a genuine character recording; **11 lack a distinct Enter recording, 4 lack Space, and 5 lack Backspace**. The source archive itself does not include separate WAVs for each missing key. Added same-pack genuine `key.character` fallback for `key.enter`, `key.space`, `key.backspace` and protected typing, preserving a distinct sample when present; no new audio synthesized or bundled.
- Added first-physical-keydown handling for Enter, Space, Backspace and Delete while **Typing Sounds** is enabled and a writable edit field has focus, independent of whether NVDA emits a typed-character callback. A following matching typed-character callback within 500 ms does not create an extra click. Keyboard Sounds mode continues to use its own physical key mappings without duplicate typing playback.
- Removed **Import old sounds folder...** button from the manager. Every preset, including bundled presets and the last one in a category, can now be deleted/removed. Bundled presets use durable user-config per-category removal records (`removed-navigation-presets.json`, etc.) so NVDA updates do not undo the choice. Users can explicitly restore removed built-ins using a separate button. Personal packs can still be deleted physically. Removed forced creation of an empty keyboard default pack, and the engine accepts an empty sound bank.
- Updated accessible English/Thai help, guides, README, event audit and version `0.11.0`; regression tests expanded to **46**, all passing. The user's transcript confirms the previous v0.10.0 commit (`d51a169`), `main` push and `v0.10.0` tag push succeeded.

## v0.11.0 verification and remaining work

- **46/46 offline tests passed** (including exact-vs-fallback events, built-in removal/restart/restore, empty preset categories, duplicate special-key prevention and previous regression checks). Built `SoundThemesForNVDA-0.11.0.nvda-addon` and `SoundThemesForNVDA-source-0.11.0.zip`; **both ZIP integrity checks passed**, the installer manifest declares `0.11.0`, and **all 706 genuine WAVs** remain. Cannot run interactive Windows NVDA inside Linux: hardware key event delivery, edit-control focus detection, wx dialog usability, installer behavior and GitHub Actions Release remain pending real NVDA / GitHub verification. 706 WAVs do not imply 706 unique dedicated events.

## Completed in v0.10.0

- Diagnosed the user's extra Shift sound from the event WAV `Speech feedback paused`. The code unconditionally played `system.paused_feedback` upon NVDA's `post_speechPaused`, which also fires when Shift pauses screen-reader speech, so switching off Navigation did not mute it. This was a *separate* root cause from the physical modifier alias bug corrected in v0.9.
- Added `pauseFeedback` config setting and Settings checkbox, **off by default**, so speech-pause system cues are opt-in. Even with the setting enabled, holding Shift or having pressed it within the previous 350 ms prevents that event sound; the physical keyboard Shift effect is unaffected. The original WAV remains installed and assignable.
- Added `event_description` explanations for named events, all dynamically listed NVDA roles/states, and the entire Windows virtual-key catalog. Specific examples say which contexts apply (Explorer file list/folder pane, browser tab, edit fields, alerts), and note unreliable historical-only automatic triggers. The editor exposes an accessible read-only description field. Users can hear descriptions when moving through the list; a 170-ms cancelable announcement ensures rapid arrowing does not build a speech backlog, while preview playback still starts independently and promptly. Bare first-letter-searchable list labels remain unchanged.
- Built version `0.10.0` installer/source distribution and updated English/Thai event explanations, help, README, feature audit and keyboard guide. GitHub push/tag and Windows NVDA in-app acceptance remain user-side verification steps.

## v0.10.0 verification and remaining work

- Offline regression tests expanded from 39 to **42** and passed. Both v0.10.0 archives passed integrity checks; the installer contains **706 genuine WAVs** and manifest version `0.10.0`. An NVDA instance is not available inside this Linux workspace, so actual key-hook timing and live speech announcement behavior remain unverified.

## Completed in v0.9.0

- Inspected the user's newly supplied `upload/effects.zip` (86 original navigation + 61 original typing PCM WAVs). Added deterministic, repeatable `scripts/import_effects_archive.py` with ZIP/WAV checks, original-byte copy, duplicate sample elimination and corrective mapping for incorrectly named old role/state events (`expended`, `invisibled`, `tablecoulmnheader`, `tableraw`).
- The new built-in `navigation/default` theme contains 85 distinct event samples; two source editable-text names map to one event. Added **59 previously uncovered original sound events** to `navigation/voiceover` without replacing any source ScreenReaderSounds audio. Existing users selecting VoiceOver therefore get more event coverage immediately; both packs remain individually selectable and do not leak audio from one to the other.
- Added eleven new typing themes from the uploaded archive and the genuine Classic Typewriter bell to the existing theme, respecting the original theme grouping. The bundle now contains **706 original PCM WAVs in 23 theme folders** under the sole packaged `globalPlugins/soundThemes/effects` root. Zero generated WAVs and zero `theme.json` files. Removed the leftover obsolete `scripts/generate_themes.py` that had mistakenly survived in the source tree.
- Fixed possible double firing of Shift/Control/Alt if NVDA raw-key hooks deliver both generic and side-specific virtual-key aliases for the same physical press; normalize left/right Shift by scan code and Control/Alt by extended bit, then trigger only on the first pressed physical key transition. Preserve distinct left/right modifier detection and normal input pass-through.
- Manifest and manuals updated to **0.9.0**. The user's PowerShell transcript confirms `git push -u origin main` succeeded for commit `aec66da`; however, GitHub Release `v0.9.0` must still be created by pushing this update and tag.

## v0.9.0 verification and remaining work

- **39/39** independent Python regression tests passed, including new event mapping, exact built-in source counts and physical Shift alias deduplication.
- Must still verify keyboard hook data (including side-specific VK conventions), actual Windows Shift playback, and whether other NVDA/Windows keyboard sound add-ons generate one of the perceived sounds. These cannot be established solely from Linux offline tests. Unrecognized historical role IDs without current NVDA Role/State counterparts remain assignable but might not have automatic OS callbacks.

## Completed in v0.8.0

- Auto-audition WAVs while changing any of the three theme selectors in the NVDA Sound Themes settings panel, any of the three theme lists in Manage Sound Themes, and the selected item in the event editor. No activation/mode change is required; missing sounds do not open popups.
- Theme list items now use only their human names, without `Built-in:`/`Custom:` prefixes. This restores native first-letter navigation (press C for Cherry). In the sound event editor removed `Role:`/`State:` labels and ` (assigned)` suffixes; letters A–Z and digits 0–9 use their characters as list labels. Category controls remain, and the exact theme/event ID still drives every action.
- Added a nonblocking, latest-only preview WAV decoding worker, an eight-recording decoded preview cache, and a generation guard against obsolete in-progress previews. It dispatches into the existing twelve-voice player and does not replace the selected theme or pollute another pack.
- Promoted release metadata to `0.8.0`; updated README, author guides, event and audio audits, and translated add-on help. GitHub Actions already builds from manifest version on pushes and releases from new `v*` tags; source instructions now distinguish updating a prior clone from a first push.

## v0.8.0 verification and remaining work

- **37/37 NVDA-independent Python regression tests passed**, including representative pack selection, first-letter searchable labels, and cancellation of a slow obsolete preview decode. All prior concurrency and original audio tests still pass.
- Real Windows NVDA wx.ListBox/Choice typeahead, real WASAPI cue timing, secure desktop and focus navigation must still be verified; no claim of fully tested live Windows accessibility until then.
- GitHub repository `nuttawat-arch/soundThemes_For_NVDA` was observed public but still empty when checked. A new `.nvda-addon` installer and source archive can be released now; publishing a GitHub Release still requires an initial source push and the `v0.8.0` tag (or a separately authorized remote release operation).

## Completed in v0.7.0

- Implemented **bounded polyphonic playback**: twelve reusable independent NVDA `nvwave.WavePlayer` voices, each with a dedicated worker, for Navigation, Typing, Keyboard and previews. A long WAV cannot block other streams and no incoming cue stops earlier playback. Each voice waits for its own playback completion (`idle`), so WAV audio never builds up in an individual native stream. In rare saturation, newest pending cues replace obsolete waiting cues rather than hanging or creating unbounded threads/buffers; not every click is guaranteed under sustained overload.
- Kept the previously required mutually exclusive feature modes (Navigation + Typing by default; Keyboard Sounds OFF by default and exclusive when enabled). Voice concurrency is *within and across currently enabled* sound categories; no accidental activation of navigation while Keyboard mode is on.
- Moved **all 510 genuine WAV files** and eleven built-in packs out of the former separate `globalPlugins/Sound Themes for NVDA/effects` directory into `globalPlugins/soundThemes/effects` alongside the executable plugin. No source WAVs were destroyed. The NVDA **user configuration** `soundThemes/effects` remains separate by design so editable packs survive upgrades.
- Removed `scripts/generate_themes.py`, the obsolete synthetic audio generator not used by the release. No synthesized WAVs or `theme.json` files are packaged.
- Updated add-on manifest developer to **Nuttawat Seecham**, contact **nutblind2545t@gmail.com**, homepage `https://github.com/nuttawat-arch/soundThemes_For_NVDA`, plus both add-on help files. Added `.gitignore`, GitHub Actions test/build/tagged-release workflow, and GitHub + NVDA Add-on Store instructions to README. Confirmed the user's repository is currently public and empty; no external push occurred.

## v0.7.0 validation and remaining work

- **34/34 NVDA-independent regression tests passed**, including mock WASAPI playback of three long overlapping sounds, independent players, bounded high-rate burst handling, and all previous source/audio mapping tests.
- Need verify actual NVDA Windows WASAPI device limits and UX timing, Windows Explorer list focus, shared audio devices, system lock/secure desktop and full keyboard capture, before claiming production-ready. GitHub Release and NVDA Add-on Store publishing remain user actions, not yet submitted.

## Completed in v0.6.0

- Inspected `upload/Sounds.zip`, containing 881 original Kliq WAVs, and imported seven real switch sets: Cherry 65, DSA 65, KAT 65, MT3 58, OEM 65, SA 64, XDA 65, including one fixed original recording per set for unrecorded keys. KAT is the fresh-install default; existing selected user themes are preserved. No key-release WAVs or unused mouse-release WAVs were packaged.
- Active add-on contains **510 genuine PCM WAVs**, 11 built-in theme folders; no synthetic audio and no `theme.json`.
- Fixed missing File Explorer item sounds: previously `State.SELECTED` masked the available `role.listitem`/`role.treeviewitem` sound. New focus policy only uses a state when its exact WAV exists, and selection events handle list/tree item navigation.
- Fixed delayed/stale playback: although the old worker already stopped the current WASAPI player before feeding a sound, its 12-item queue could still retain obsolete focus cues. Now the queue holds only the latest pending cue, and the worker skips any newly superseded entry. Keyboard samples enqueue synchronously with raw-key decisions instead of via wx.CallAfter.
- Prevented false tree-collapse audio when merely leaving a tree view, excessive state-change combinations, repeated identical focus/selection sounds within 75 ms, and caret callbacks caused by ordinary typing.
- Added a reproducible Kliq importer `scripts/import_kliq_audio.py`, static and runtime-independent tests for key mapping/fallback, real audio import, Explorer selected-role choice, and newest-sound queue behavior. Bundled Kliq MIT copyright/license in `doc/KLIQ_LICENSE.txt`.

## Validation and limitations

- **32/32 Python regression tests passed** during v0.6.0 development.
- Built installer `SoundThemesForNVDA-0.6.0.nvda-addon` and source `SoundThemesForNVDA-source-0.6.0.zip`. Both ZIP integrity checks passed. The installer includes **510 PCM WAVs**, **zero `theme.json`** files and a valid manifest version `0.6.0`. Both archives are approximately **7 MB** after compression, with no bundled unused Kliq key-release audio.
- Cannot run a real Windows NVDA 2026 instance in this Linux environment; focus tracking, Windows UI dialogs, secure/lock screens and actual WASAPI timing must be confirmed on Windows before calling this fully validated.
- Kliq provides no dedicated audio for every F/media/hardware key; its real in-pack fallback covers events that Windows/NVDA actually delivers, without claiming a distinct recording for all 255 keys.

## Completed in v0.5.0

- Inspected updated `upload/ScreenReaderSounds.zip`, now audio-bearing: 50 WAVs, 24 nested `objdata.zip` role WAVs and three OGG recordings; imported 54 distinct event assignments. With previous original navSounds assets the add-on now ships **62 real PCM WAV files**, 0 synthetic samples.
- Added third `Keyboard Sounds` category, OFF by default, with `effects/keyboard/{pack}` folder. Navigation and Typing remain ON by default. Enabling Keyboard disables both of them, and enabling either Navigation or Typing disables Keyboard. System/lock sound option remains separate.
- Added all Windows VK 1–255 assignable key IDs, F1–F24, separate modifiers, media/volume/browser, numpad, punctuation, and optional brightness/Fn events. A missing per-key WAV stays silent. Exact one-file playback; no randomness for Keyboard Sounds.
- Kept navigation event-driven: no raw Tab, arrows, Home, End or Page keypress sound when Keyboard Sounds is off. Actual focus, role, browse, caret and scroll movements still have navigation feedback.
- One Manage Sound Themes button opens three keyboard-accessible wx notebook tabs (Navigation, Typing, Keyboard). One Open Sound Folders button. Keyboard event editor can capture a focused physical key, move to its assigned event and preview its WAV. Arbitrary WAV filenames are renamed canonically on assignment.
- Original roles from nested SRS archive override duplicated flat-role sounds; three OGG files were decoded to genuine PCM WAV offline. No manifests or timed sound sprite are used at runtime.
- Added `KEYBOARD_SOUNDS_GUIDE.md`, updated README/audio provenance and online download guidance. Source tests expanded to keyboard modes/keys and full SRS flat+nested format.

## Still pending

- Full independent Mechvibes per-key WAV pack has not been provided; built-in keyboard/voiceover currently has only three true SRS samples (Backspace, End and Shift+Tab). Do not claim all 255 keys audible out of the box.
- Hardware Fn/dim keys may not reach NVDA's raw-key hook. Speech pause now has the documented `post_speechPaused` callback, but tutorial, long click and volume-beep recordings remain preserved/assignable without confirmed NVDA 2026 runtime triggers; independent TalkBack 5/6 audio was not supplied.
- Must test a running NVDA 2026 on Windows, including accessibility of wx notebook/capture, keyboard input callback details, secured session audio and modifier handling. Unit tests and ZIP checks alone are insufficient.

## v0.5.0 release verification

- **28/28 Python regression tests passed** on 2026-10-24, including updated SRS flat+nested archive handling and keyboard pack/no-random/mode checks.
- **12 Python sources parsed successfully.** The `.nvda-addon` archive integrity check passed with **74 packaged files, 62 PCM WAV recordings, no `theme.json`**. Manifest version: `0.5.0`. English and Thai add-on help included.
- Source archive contains the add-on code, the real WAV assets, tests, importer and documentation. Its archive integrity check passed.
- No Windows NVDA 2026 runtime certification has been performed; any UI interaction or hardware-key coverage observations remain hypotheses until tested by the user.

## Previous release audit (v0.4.0, retained as history)

## Source audit (2026-10-23)

- Inspected the original code-only `upload/navSounds.zip` v2.2.0 and the *previous* `upload/ScreenReaderSounds.zip` v3.0.1BETA; neither had actual WAV assets at that time. Superseded by the audio-bearing archive described above.
- Compared all 21 ScreenReaderSounds named cues, dynamic NVDA roles/states, browse mode, keyboard, mouse, lock/unlock and theme controls. Details and behavioral qualifications: `FEATURE_AUDIT.md`.
- Read supplied Python Pro, Python Testing Patterns and Accessibility Audit skills; reviewed modern NVDA extension points.

## Implemented in v0.4.0

- One configurable `soundThemes` plugin for navigation, typing, system and mouse events; volume and role/state speech options.
- **WAV-only theme structure**: `globalPlugins/Sound Themes for NVDA/effects/{navigation,typing}/{pack}/*.wav`. No `theme.json` is needed or bundled in new theme directories; executable Python is in `globalPlugins/soundThemes/`.
- Two independent theme lists/selectors/managers. Random typing WAVs come **exclusively from the active typing pack**. ScreenReaderSounds' 21 named WAVs and original role/state filenames can be imported and converted.
- Accessible wxPython theme editor and settings; create, clone, rename, delete, assign, preview, choose and export/import WAV folder/ZIP packs.
- `k.is_pressed()`-style pressed key state tracking using **NVDA's existing raw-key extension** instead of packaging the extra low-level global keyboard hook. Media, Shift+Tab and navigation keys supported.
- Modern session lock/unlock and lockscreen follow-up; separate secure-desktop state listener where NVDA provides it. Configurable delayed mouse hover with noisy background roles ignored.
- Dynamic Role/State event listing, browse mode (including reversible fallback), object events, PCM WAV cache using NVDA `nvwave` without BASS.
- v0.1 user theme splitting without original deletion; v0.2 theme.json packs converted with complete originals moved to `soundThemes/legacy-backups/`.
- Real audio downloaded from the official navSounds sound store: **15 original Voiceover navigation WAVs** and **6 original Classic Typewriter WAVs**. They are shipped untouched at `navigation/voiceover` and `typing/classic-typewriter`, with no synthetic sound recordings in the new package.
- A source-aware original-WAV importer (`scripts/import_original_audio.py`) merges an audio-bearing ScreenReaderSounds add-on when available. It handles role files and special files for VoiceOver, TalkBack 5.0.7 and TalkBack 6+, resolves duplicate event mappings with ScreenReaderSounds priority and distinguishes role `tab.wav` from keystroke `Tab.wav`.
- Previous v0.3 synthetic packs were moved to `soundThemes-synthetic-v0.3.0-backup/`, recoverably outside the active project; the synthetic generator was removed.
- Independent regression suite: **22 tests**, including ZIP safety, migration/backups, old and new cue mapping, pack isolation, original audio merge precedence and key state.

## Verification and outstanding work

- All Python files compiled and **22/22 tests passed in a writable Python 3.12 test session**; v0.4 archive packaging validation is tracked at delivery.
- **BLOCKED for complete two-project audio parity:** both uploaded source ZIPs contain zero WAV files. The listed full ScreenReaderSounds installer (~14 MB) could not be downloaded from its host (HTTP 403). Thus VoiceOver/TalkBack sounds originally bundled by ScreenReaderSounds are not yet present. A complete audio-bearing copy must be provided before this can be called a complete original-sound merge. See `SOUND_SOURCES.md`.
- **Not verified under Windows NVDA 2026:** real extension callback signatures, keyboard timing, system/secure-desktop audio, mouse hover, settings accessibility, audio device switching and third-party coexistence. Do not call it production-certified yet.
- Role and State enumerations are complete for the installed NVDA instance, but not every possible application event can be captured without an NVDA callback. Secure screens require NVDA's approved system configuration and have security restrictions.
- Windows testing next: portable NVDA 2026.1/2026.2; mouse; shortcuts; browse; speech; lock/unlock; secure desktop; updates of old personal themes; ZIP export/import.
