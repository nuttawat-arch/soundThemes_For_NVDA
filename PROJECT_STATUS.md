# Sound Themes for NVDA — Project status v0.9.0 (2026-10-24)

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
