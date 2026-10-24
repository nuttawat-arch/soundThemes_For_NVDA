# Sound Themes for NVDA 0.16.0

**New in 0.15.0:** Open the complete Sound Themes settings window directly
from **NVDA menu → Tools → Sound Themes settings...**. It is no longer buried
under NVDA Preferences → Settings. The standalone, keyboard-accessible dialog
has **OK** and **Cancel** buttons and retains all three pack managers, event
editor, volume and enable switches. Configuration values remain in NVDA's
normal configuration to preserve existing choices; only the **location of the
user interface** has changed.

GitHub Releases provide **optional update notifications without the NVDA Add-on
Store**. Automatic checks are enabled initially, begin 15 seconds after NVDA
starts, and perform HTTP/network and file I/O in a background thread. In Tools
→ Sound Themes settings, choose **Check for updates now** or uncheck **Check for
updates when NVDA starts**. An available update offers **Update now**, **Later**,
or **Skip this version**. The installer still asks for user confirmation and
NVDA restart. Only a stable release containing the correctly named add-on
from `nuttawat-arch/soundThemes_For_NVDA` is accepted. When GitHub provides an
SHA-256 digest, it is checked before installation. Installing an updated add-on
can replace custom WAVs inside it; **export edited presets as ZIPs first**.

The private developer script **`release.ps1`** runs tests, updates the version,
builds/validates both archives, commits and pushes `main` plus its `vX.Y.Z`
tag. GitHub Actions then builds and publishes a Release automatically. The
script is deliberately **excluded from Git and from both distributable ZIPs**;
keep your own local copy at the repository root. It does not submit anything
to the NVDA Add-on Store. The iPhone Keyboard and VoiceOver typing presets
have also been compared: despite similar audible character, their source WAVs
and decoded waveforms are different, so neither has been deleted.

**New in 0.14.0:** All sound presets are editable directly within the add-on's
`globalPlugins/soundThemes/effects/` directory: rename, replace WAVs or delete
any of them without copying a "built-in" preset. The add-on no longer creates
the separate `NVDA user-config/soundThemes/effects/` sound folder. Existing
user-config packs from 0.13 are **copied once** into the embedded effects folder
on the first upgraded launch, with collisions given a `-personal` suffix. Old
files are intentionally left untouched for safety. Small playback preferences
and removal decisions live in NVDA's existing settings, not another WAV folder.
**Important:** reinstalling/updating any NVDA add-on can replace its installed
files, including edited WAVs. **Export personalized packs to ZIP before every
add-on update**; this is the necessary trade-off when storing writable sounds
inside the installed add-on instead of NVDA's persistent user configuration.

Keyboard Sounds has **two** per-preset methods: "Two layers" plays dedicated
press and release files; "One layer" plays the combined file only on keydown.
The former third "press-only" choice is migrated to "One layer" without losing
the selected preset. Key audio has no unnecessary fixed 18 ms throttle, and
when Navigation is disabled expensive web Browse Mode caret snapshots are
skipped entirely. Output-device resolution is done once per queued sound.

The sound editor now has a single alphabetically ordered list (no category
chooser), familiar names such as `checkbox`, `editabletext`, `typekey`, and
`typekeyremove`, plus **Done** and **Cancel**. Cancel restores every WAV change
made during that edit session. Legacy plain WAV filenames are accepted; when
`checkbox.wav` and `role.checkbox.wav` coexist, the plain original is used
instead of randomly alternating. The new user-supplied ScreenReaderSounds ZIP
added TalkBack and updated VoiceOver navigation/typing recordings. Original
ScreenReaderSounds takes win on canonical event conflicts over navSounds.

Maintainer: **Nuttawat Seecham** — nutblind2545t@gmail.com  
Source and homepage: https://github.com/nuttawat-arch/soundThemes_For_NVDA

One accessible NVDA add-on combining **navSounds** and **ScreenReaderSounds** behaviors with individually assignable **Keyboard Sounds**. All built-in audio is genuine. No `theme.json` files or generated recordings are bundled.

## Three independent sound folders, two mutually exclusive modes

| Feature | Default | Behavior |
|---|---|---|
| Navigation | **On** | Plays real NVDA role/focus/state/browse/caret/selection/scroll events, not raw key presses |
| Typing | **On** | Plays typed characters and typing-specific events; random samples stay inside the active typing pack |
| Keyboard Sounds | **Off** | Plays per-key down/up cues according to each preset's playback mode; never random |

Enabling **Keyboard Sounds** automatically disables **both** Navigation and Typing. Re-enabling either Navigation or Typing disables Keyboard Sounds. System sounds (including lock/unlock) use a separate switch.

When Keyboard Sounds is off, simply pressing Tab, arrows, Home/End or Page Up/Down never triggers a raw key sound. An actual NVDA focus/browse/scroll transition can still play a distinct navigation sound.

## Accessible management

**New in 0.13, simplified in 0.14: physical keydown/keyup sounds.** In Manage sound themes → Keyboard Sounds, each editable preset has one of **two** playback modes: **Two layers** (a different press and release WAV), or **One layer** (a combined press-and-release WAV played only once on keydown). `keyboard.a.wav` is the keydown file; `keyboard.a__release.wav` is the optional keyup file. An old 0.13 "Press only" selection is recognized as **One layer**. The keyboard editor has Replace/Preview/Remove **release WAV** controls. The NVDA raw-key listener suppresses held-key auto-repeat and generic/left/right modifier duplicate reports, differentiates numpad Enter and nonextended numpad navigation keys, never intercepts Windows/NVDA shortcuts and no longer delays genuine rapid key presses with an arbitrary 18 ms minimum gap. Mode preferences live in native NVDA settings; keyboard ZIP exports/imports preserve them.

All seven Kliq switch presets now include their original `*-up.wav` samples in addition to the key-down files already present. The new **Bucklespring** preset uses actual IBM Model M recordings: its upstream `NN-1.wav` means key **down** and `NN-0.wav` means key **up**. Bundled keyboard presets containing release recordings default to separate playback unless a saved mode override exists; older custom press-only presets keep their current behavior. Bucklespring's original audio is provided under **GNU GPL v2** with its full license in `doc/BUCKLESPRING_LICENSE.txt`. No audio is generated.

**New in 0.12: Browse Mode sounds for website controls.** The actual 0.11 audio already contains role recordings for buttons, links, headings, checkboxes, radio buttons and menu items in both Navigation presets. The missing feedback came from event handling: moving NVDA's virtual Browse Mode caret inside a browser often doesn't emit a keyboard `event_gainFocus`. The attempted `visionHandlerExtensionPoints.post_browseModeMove` registration referenced a module instead of a real event instance, and the backup Quick Navigation wrapper accidentally called the caret movement function with the wrong arguments because its saved closure was overwritten. Both problems are fixed. When Browse Mode moves with arrows or single-letter shortcuts (`B` for button, `K` for link, `H` for heading, and other NVDA quick navigation types), the add-on now identifies the new web element and plays **one corresponding role cue**. It prefers a focusable link/button ancestor over a static text leaf; if no semantic role is found it uses the existing caret sound. The reversible hooks do not swallow any keys or require new WAVs. Real browser/Windows timing needs user acceptance testing.

Open NVDA menu → **Tools → Sound Themes settings...** and select the desired active theme packs. **Manage sound themes...** opens Navigation, Typing and Keyboard Sounds pages; each has Create/Copy, Edit, Rename, Delete, Import/Export ZIP and Use This Theme. The old **Import old sounds folder...** button remains removed. **All packs can be renamed, edited and deleted directly**, including presets supplied by the installer. The **Open sound folders** button opens the add-on's own effects directory. The **Edit sounds** dialog lists events alphabetically without category filters; it includes Done to keep edits and Cancel to undo all WAV changes made in that edit session.

**New in 0.11: Enter, Space and Backspace typing coverage and unrestricted preset removal.** NVDA does not consistently send typed-character events for these keys in every editor. Typing Sounds observes the first physical keydown **only while an editable text field is focused**, using NVDA's raw-key callback, and suppresses a matching later typed-character duplicate. Delete shares the Backspace typing sound. If a typing pack lacks a distinct Enter/Space/Backspace recording, the matching key plays its own genuine general character WAV; it never borrows from another pack. In 0.14 all folders are user-editable within the add-on. Deletion choices are remembered in native NVDA settings even if a later reinstall makes a packaged folder appear on disk again; the sound pack is not forced back into the list. Export WAV ZIP backups before upgrades.

**New in 0.8: hear each sound as you navigate.** Arrow through the Navigation, Typing or Keyboard theme chooser in NVDA Settings, or through the theme list in the manager, to audition a real representative WAV from that exact pack without activating it. The event editor likewise previews each assigned event when its list selection moves. A missing WAV stays silent; no modal message interrupts arrowing. Previews decode in a latest-only background worker, so rapidly changing the highlighted item does not block the dialog or play a backlog of outdated previews. All other audio playback continues through the existing polyphonic sound engine.

**New in 0.9: Shift double-sound prevention and complete supplied effects archive.** Raw generic Shift/Control/Alt codes and their side-specific Windows aliases now resolve to the same held physical key, so duplicate reports during one press cannot trigger two independent sound effects. The newly supplied `effects.zip` contributed all **86 original navSounds/default** and **61 typing** source recordings. The built-in `navigation/default` theme has **85 distinct assigned WAVs** after two source names for editable text were combined; **59 previously missing cues** also fill gaps in `navigation/voiceover` without overwriting any existing ScreenReaderSounds recording. The twelve typing packs from that archive remain independently selectable, and identical audio within an event is not copied twice. All built-in sounds remain unmodified original WAV bytes. As before, external add-ons or Windows sticky-key alerts may make their own additional sounds and must be investigated separately if a double sound remains.

**New in 0.10: actual Shift speech-pause double-sound fix.** NVDA emits its `post_speechPaused` notification when the Shift key pauses speech. Earlier versions played `system.paused_feedback` in response, separately from the physical Shift recording, so **turning off Navigation could not silence this sound**. The new **Play speech-pause feedback** option is **off by default**; even when enabled, ordinary Shift presses are excluded using held/recent Shift detection. The original `system.paused_feedback` recording is still available for preview, reassignment and non-Shift speech-pause events. Disabling this system cue does not disable physical Shift sounds in Keyboard Sounds mode. Existing configurations keep all other sound settings unchanged.

**New event explanations.** In the sound editor, moving through events still previews their WAV. A separate **Description of selected sound event** read-only text field explains what each event means and where it can happen—for example `LISTITEM` in the File Explorer file list, `TREEVIEWITEM` in Explorer's folder pane, or `TAB` in a browser. The **Speak the event description when moving through the list** checkbox is on by default. Descriptions are spoken only after a short pause in navigation, cancelling older pending explanations so rapidly arrowing through events remains responsive. Press Tab to focus and read the full description independently at any time. Descriptions distinguish real NVDA callbacks from legacy placeholders not yet wired to automatic triggers. Neither descriptions nor category names are inserted into searchable event labels or sound filenames.

Theme list items are named simply `Cherry`, `DSA`, `KAT`, etc., **not** `Built-in: Cherry` or `Custom: Cherry`: type `C` in the list to find Cherry. The event list also omits redundant `Role:` / `State:` prefixes and assignment suffixes; key labels `A`–`Z` and `0`–`9` begin directly with those characters for first-letter lookup. Categories are still available in their separate category control. The selected theme's source and internal identifier are retained for operations without being added to the audible list name.

In the keyboard editor, navigate to **Capture and preview a physical key**. Press any accessible key: the editor selects that physical-key event and immediately previews its assigned WAV. Outside the capture field, Tab/Escape still navigate normally. Choose **Replace WAV** for a press/combined sample and **Replace key release WAV** for a separate release sample. The editor saves them as `keyboard.a.wav` and `keyboard.a__release.wav`, regardless of source filenames. There is no random-variation button for keyboard packs. Real Kliq fallback recordings serve missing keys within the same pack, with separate press/release defaults; custom packs without fallbacks remain silent.

Read [KEYBOARD_SOUNDS_GUIDE.md](KEYBOARD_SOUNDS_GUIDE.md) for full details, examples, and verified download links.

## Sound storage

```text
globalPlugins/soundThemes/effects/
    navigation/default/role.listitem.wav
    navigation/default/role.tablecolumnheader.wav
    navigation/voiceover/role.button.wav
    navigation/voiceover/system.lock.wav
    typing/classic-typewriter/key.character__original.wav
    typing/voiceover/key.space.wav
    keyboard/voiceover/keyboard.shift_tab.wav
    keyboard/kat/keyboard.a.wav
    keyboard/kat/keyboard.a__release.wav
    keyboard/kat/keyboard.default.wav
    keyboard/bucklespring/keyboard.numpad_enter.wav
    keyboard/bucklespring/keyboard.numpad_enter__release.wav

# Personal and shipped packs are now all in the add-on tree shown above.
# Keyboard mode and removed-name preferences use NVDA's existing settings.
```

The executable Python files and all WAV assets live under **one `globalPlugins/soundThemes/` directory inside the installed add-on**. This deliberately stops creating the old `NVDA user-config/soundThemes/effects/` folder. Sound packs need only `.wav` files, no JSON theme manifest. Because add-on reinstalls replace the contents of the installed folder, **export any modified packs before installing a newer version**.

## Source audio and compatibility

The original `upload/ScreenReaderSounds.zip` added 54 assignments. The new `upload/ScreenReaderSounds(1).zip` contains distinct VoiceOver and TalkBack folders plus nested VoiceOver role recordings. Its original WAV/OGG material is now included in Navigation and Typing; ScreenReaderSounds wins when an event also exists in navSounds. Kliq and Bucklespring supply physical press/release keyboard audio. The current bundle contains **1,398 genuine WAVs across 26 editable folders**, with no synthesized audio. See [SOUND_SOURCES.md](SOUND_SOURCES.md) and [FEATURE_AUDIT.md](FEATURE_AUDIT.md).

**Eight switch keyboard themes** are now available: Bucklespring, Cherry, DSA, KAT (new-install default), MT3, OEM, SA and XDA. Every recorded key maps from the original scan code to real canonical press/release WAVs; a missing key may use the same pack's fixed genuine fallback of the correct phase (no randomness/mixing). The additional `keyboard/voiceover` theme remains available. Hardware-specific Fn/brightness buttons may not emit Windows keyboard events visible to NVDA. Some legacy ScreenReaderSounds event IDs remain assignable but not wired to dependable runtime triggers.

Explorer item navigation prioritizes the real `role.listitem`/`role.treeviewitem` sample over unavailable `state.selected`. **Up to twelve sounds play concurrently**, through independent reusable NVDA WASAPI players. Long navigation WAVs do not stop or block another navigation or typing sample. The audio queue is bounded, discarding superseded *pending* cues only when the streams are busy; there is no unbounded playback backlog. This also applies to Keyboard Sounds when that mode is enabled. The existing rule that Keyboard Sounds disables Navigation and Typing remains intact. Test live responsiveness on Windows NVDA before considering it production-verified.

## Build, test and install

```bash
python -B -m unittest discover -s tests -v
python scripts/build.py
python scripts/build_source.py
```

Run these commands **from the `soundThemes` source directory**. All real imported WAVs are already bundled. Developers with original archives can rerun `python scripts/import_kliq_audio.py ../upload/Sounds.zip`, `python scripts/import_bucklespring_audio.py ../upload/bucklespring-master.zip` and `python scripts/import_screenreader_multitheme.py '../upload/ScreenReaderSounds(1).zip'`. Install `SoundThemesForNVDA-0.15.0.nvda-addon` via NVDA's add-on manager, restart NVDA and disable other running keyboard/navigation audio add-ons if you hear duplicate effects. Before upgrading again, export any edited packs to ZIP. Try portable NVDA first: offline tests do **not** prove hardware event delivery, secure desktop playback or live wx dialog accessibility on Windows.
Run these commands **from the `soundThemes` source directory**. All real imported WAVs are already bundled. Developers with original archives can rerun `python scripts/import_kliq_audio.py ../upload/Sounds.zip`, `python scripts/import_bucklespring_audio.py ../upload/bucklespring-master.zip` and `python scripts/import_screenreader_multitheme.py '../upload/ScreenReaderSounds(1).zip'`. Install `SoundThemesForNVDA-0.15.0.nvda-addon` via NVDA's add-on manager, restart NVDA and disable other running keyboard/navigation audio add-ons if you hear duplicate effects. Before upgrading again, export any edited packs to ZIP. Try portable NVDA first: offline tests do **not** prove hardware event delivery, secure desktop playback or live wx dialog accessibility on Windows.

## Publishing to GitHub and the NVDA Add-on Store

Your `git push origin main` for commit `17eec09` and `git push origin v0.12.0` **both completed successfully**, according to your PowerShell transcript. You have **not confirmed publishing 0.13.0 or 0.14.0**, so use the **0.15.0 source** ZIP for this new update. Unpack it and copy its `soundThemes` folder contents into the **existing** GitHub repository folder. Do not `git init`, clone again, re-add `origin` or reuse a tag. LF→CRLF warnings are ordinary line-ending notices.

### One-command release on Windows (recommended)

Download the **separate** `release.ps1` file and place it **directly in**
`D:\NVDA\soundThemes` next to `manifest.ini`. It is intentionally absent from
the source ZIP and ignored by Git. On first use, release 0.15.0 explicitly:

```powershell
cd D:\NVDA\soundThemes
powershell -NoProfile -ExecutionPolicy Bypass -File .\release.ps1 -Version 0.15.0
```

For later patch versions, omit `-Version`; it increments the current patch
number. Supply `-Version 0.16.0` to choose a new minor version. Use `-DryRun`
to check the intended version without changing files or contacting GitHub.
The script requires Python, Git and normal GitHub authentication already set
up, refuses the wrong repository/branch and existing tags, and aborts on tests
or build errors. The tag triggers the included GitHub Actions release workflow.
**Review and export your custom audio before running an update.**

### Manual release (alternative)

```powershell
cd D:\NVDA\soundThemes
git pull --ff-only origin main
# Now copy all files from inside the extracted v0.15.0 soundThemes folder here.
git add -A
git -c user.name="Nuttawat Seecham" -c user.email="nutblind2545t@gmail.com" commit -m "Release Sound Themes for NVDA 0.15.0"
git push origin main
git tag v0.15.0
git push origin v0.15.0
```

On `main` pushes, the included GitHub Actions workflow runs tests and packages a downloadable artifact. Pushing the **new** `v0.15.0` tag creates a separate GitHub Release with the actual `.nvda-addon` installer. The release appears only once its GitHub Actions workflow succeeds. GitHub authentication may be required (e.g. Git Credential Manager). This GitHub Release mechanism **does not require submitting to the NVDA Add-on Store**. The optional Store submission procedure is documented at [NVDA Add-on Store submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md).

Sources: [navSounds](https://github.com/ahmedthebest31/navsounds), [official navSounds sound store](https://ahmedthebest31.github.io/navsounds/store/), ScreenReaderSounds files provided by the user, [Kliq (MIT; sound recordings by Cris)](https://github.com/crafter-station/kliq), [Bucklespring (GPL-2.0)](https://github.com/zevv/bucklespring), [NVDA developer documentation](https://download.nvaccess.org/documentation/developerGuide.html). See `doc/KLIQ_LICENSE.txt` and `doc/BUCKLESPRING_LICENSE.txt`.
