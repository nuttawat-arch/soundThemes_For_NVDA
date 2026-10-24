# Sound Themes for NVDA 0.12.0

Maintainer: **Nuttawat Seecham** — nutblind2545t@gmail.com  
Source and homepage: https://github.com/nuttawat-arch/soundThemes_For_NVDA

One accessible NVDA add-on combining **navSounds** and **ScreenReaderSounds** behaviors with individually assignable **Keyboard Sounds**. All built-in audio is genuine. No `theme.json` files or generated recordings are bundled.

## Three independent sound folders, two mutually exclusive modes

| Feature | Default | Behavior |
|---|---|---|
| Navigation | **On** | Plays real NVDA role/focus/state/browse/caret/selection/scroll events, not raw key presses |
| Typing | **On** | Plays typed characters and typing-specific events; random samples stay inside the active typing pack |
| Keyboard Sounds | **Off** | Plays exactly one assigned WAV for each distinct physical-key down; never random |

Enabling **Keyboard Sounds** automatically disables **both** Navigation and Typing. Re-enabling either Navigation or Typing disables Keyboard Sounds. System sounds (including lock/unlock) use a separate switch.

When Keyboard Sounds is off, simply pressing Tab, arrows, Home/End or Page Up/Down never triggers a raw key sound. An actual NVDA focus/browse/scroll transition can still play a distinct navigation sound.

## Accessible management

**New in 0.12: Browse Mode sounds for website controls.** The actual 0.11 audio already contains role recordings for buttons, links, headings, checkboxes, radio buttons and menu items in both Navigation presets. The missing feedback came from event handling: moving NVDA's virtual Browse Mode caret inside a browser often doesn't emit a keyboard `event_gainFocus`. The attempted `visionHandlerExtensionPoints.post_browseModeMove` registration referenced a module instead of a real event instance, and the backup Quick Navigation wrapper accidentally called the caret movement function with the wrong arguments because its saved closure was overwritten. Both problems are fixed. When Browse Mode moves with arrows or single-letter shortcuts (`B` for button, `K` for link, `H` for heading, and other NVDA quick navigation types), the add-on now identifies the new web element and plays **one corresponding role cue**. It prefers a focusable link/button ancestor over a static text leaf; if no semantic role is found it uses the existing caret sound. The reversible hooks do not swallow any keys or require new WAVs. Real browser/Windows timing needs user acceptance testing.

Open NVDA menu → Preferences → Settings → **Sound Themes**. Select three active theme packs. The single **Manage sound themes...** button opens a dialog with **Navigation**, **Typing** and **Keyboard Sounds** tabs. Each has Create/Copy, Edit, Rename, Delete, Import ZIP, Restore removed presets, Export ZIP and Use This Theme. The old **Import old sounds folder...** button has been removed. Built-in packs are read-only for editing (copy to a personal theme first), **but every pack may be removed from the list, including built-ins**. The single **Open sound folders** button opens the NVDA user effects root.

**New in 0.11: Enter, Space and Backspace typing coverage and unrestricted preset removal.** NVDA does not consistently send typed-character events for these keys in every editor. When Typing Sounds is enabled, the add-on now observes their first physical keydown **only while an editable text field is focused**, using NVDA's existing raw-key callback, and suppresses a matching later typed-character duplicate. Delete shares the Backspace typing sound. If the chosen typing pack has no separate `key.enter.wav`, `key.space.wav` or `key.backspace.wav`, the corresponding key plays a real `key.character.wav` sample from **that same pack**. Dedicated WAVs take precedence; empty packs stay silent. This is a playback fallback, **not an invented recording**: the 13 bundled typing packs do not all have dedicated recordings. Every built-in preset may be hidden persistently (including the last one) and restored through **Restore removed presets**; this preference survives add-on updates in NVDA user config. Personal theme deletion removes its files after confirmation. No preset is mandatory and no empty default is automatically created.

**New in 0.8: hear each sound as you navigate.** Arrow through the Navigation, Typing or Keyboard theme chooser in NVDA Settings, or through the theme list in the manager, to audition a real representative WAV from that exact pack without activating it. The event editor likewise previews each assigned event when its list selection moves. A missing WAV stays silent; no modal message interrupts arrowing. Previews decode in a latest-only background worker, so rapidly changing the highlighted item does not block the dialog or play a backlog of outdated previews. All other audio playback continues through the existing polyphonic sound engine.

**New in 0.9: Shift double-sound prevention and complete supplied effects archive.** Raw generic Shift/Control/Alt codes and their side-specific Windows aliases now resolve to the same held physical key, so duplicate reports during one press cannot trigger two independent sound effects. The newly supplied `effects.zip` contributed all **86 original navSounds/default** and **61 typing** source recordings. The built-in `navigation/default` theme has **85 distinct assigned WAVs** after two source names for editable text were combined; **59 previously missing cues** also fill gaps in `navigation/voiceover` without overwriting any existing ScreenReaderSounds recording. The twelve typing packs from that archive remain independently selectable, and identical audio within an event is not copied twice. All built-in sounds remain unmodified original WAV bytes. As before, external add-ons or Windows sticky-key alerts may make their own additional sounds and must be investigated separately if a double sound remains.

**New in 0.10: actual Shift speech-pause double-sound fix.** NVDA emits its `post_speechPaused` notification when the Shift key pauses speech. Earlier versions played `system.paused_feedback` in response, separately from the physical Shift recording, so **turning off Navigation could not silence this sound**. The new **Play speech-pause feedback** option is **off by default**; even when enabled, ordinary Shift presses are excluded using held/recent Shift detection. The original `system.paused_feedback` recording is still available for preview, reassignment and non-Shift speech-pause events. Disabling this system cue does not disable physical Shift sounds in Keyboard Sounds mode. Existing configurations keep all other sound settings unchanged.

**New event explanations.** In the sound editor, moving through events still previews their WAV. A separate **Description of selected sound event** read-only text field explains what each event means and where it can happen—for example `LISTITEM` in the File Explorer file list, `TREEVIEWITEM` in Explorer's folder pane, or `TAB` in a browser. The **Speak the event description when moving through the list** checkbox is on by default. Descriptions are spoken only after a short pause in navigation, cancelling older pending explanations so rapidly arrowing through events remains responsive. Press Tab to focus and read the full description independently at any time. Descriptions distinguish real NVDA callbacks from legacy placeholders not yet wired to automatic triggers. Neither descriptions nor category names are inserted into searchable event labels or sound filenames.

Theme list items are named simply `Cherry`, `DSA`, `KAT`, etc., **not** `Built-in: Cherry` or `Custom: Cherry`: type `C` in the list to find Cherry. The event list also omits redundant `Role:` / `State:` prefixes and assignment suffixes; key labels `A`–`Z` and `0`–`9` begin directly with those characters for first-letter lookup. Categories are still available in their separate category control. The selected theme's source and internal identifier are retained for operations without being added to the audible list name.

In the keyboard editor, navigate to **Capture and preview a physical key**. Press any accessible key: the editor selects that physical-key event and immediately previews its assigned WAV. Outside the capture field, Tab/Escape still navigate normally. Select **Replace WAV** to choose a file from anywhere, regardless of filename; the editor saves it as `keyboard.a.wav`, `keyboard.f7.wav`, etc. There is no random-variation button for keyboard packs. Kliq packs have a genuine in-pack fallback sample for keys not individually recorded; custom packs without a fallback remain silent on missing bindings.

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
    keyboard/kat/keyboard.default.wav

NVDA user-config/soundThemes/effects/
    navigation/<pack>/*.wav
    typing/<pack>/*.wav
    keyboard/<pack>/*.wav
```

The executable Python files and all bundled WAV assets now share **one `globalPlugins/soundThemes/` directory**. The second path is NVDA's separate *writable user configuration*, required so personal themes survive upgrades; it is not an extra bundled asset folder. Sound packs need only `.wav` files, not a theme manifest.

## Source audio and compatibility

The audio-bearing `upload/ScreenReaderSounds.zip` contains 50 top-level WAVs, another 24 WAVs inside `objdata.zip`, plus three original OGG recordings. Its source produced **54 unique canonical event assignments**, with inner role recordings taking precedence on duplicates and original OGG recordings decoded offline to real PCM WAVs. The seven real Kliq keyboard sets came from `upload/Sounds.zip`. **Version 0.9.0 adds the 86 navigation and 61 typing recordings from `upload/effects.zip`, for a total of 706 genuine WAVs in 23 distinct built-in folders** after merging event/file duplicates. No audio was synthesized. The Kliq importer intentionally omits unused key-release files. See [SOUND_SOURCES.md](SOUND_SOURCES.md) and [FEATURE_AUDIT.md](FEATURE_AUDIT.md).

**Seven built-in keyboard themes** are now available: Cherry, DSA, KAT (new-install default), MT3, OEM, SA and XDA. Every recorded key maps directly from its original scan code to one canonical WAV; a missing key uses the same pack's fixed, genuine `keyboard.default.wav` (no randomness or mixing packs). The additional original `keyboard/voiceover` theme remains available. Hardware-specific Fn/brightness buttons may not emit Windows keyboard events visible to NVDA. Some legacy ScreenReaderSounds event IDs are stored for later support but are not yet wired to dependable runtime triggers.

Explorer item navigation prioritizes the real `role.listitem`/`role.treeviewitem` sample over unavailable `state.selected`. **Up to twelve sounds play concurrently**, through independent reusable NVDA WASAPI players. Long navigation WAVs do not stop or block another navigation or typing sample. The audio queue is bounded, discarding superseded *pending* cues only when the streams are busy; there is no unbounded playback backlog. This also applies to Keyboard Sounds when that mode is enabled. The existing rule that Keyboard Sounds disables Navigation and Typing remains intact. Test live responsiveness on Windows NVDA before considering it production-verified.

## Build, test and install

```bash
python -B -m unittest discover -s tests -v
python scripts/build.py
python scripts/build_source.py
```

Run these commands **from the `soundThemes` source directory**. To reimport the newly supplied files in the developer workspace, run `python scripts/import_effects_archive.py ../upload/effects.zip` if the archive is present; it is *not* required at runtime or for GitHub builds because all selected original WAVs are included in source. Install `SoundThemesForNVDA-0.12.0.nvda-addon` using NVDA's add-on manager, restart NVDA, and disable old navSounds/ScreenReaderSounds or standalone keyboard-sound add-ons to avoid duplicate feedback. Existing selected `voiceover` remains active and gains 59 missing events; Navigation `default` can also be chosen. Try portable NVDA 2026 first: static Python tests outside Windows do **not** prove hardware event delivery, secure-desktop playback or accessible Windows wx dialogs.

## Publishing to GitHub and the NVDA Add-on Store

Your `git push origin main` for commit `d51a169` and `git push origin v0.10.0` **both completed successfully**, according to your PowerShell transcript. The LF→CRLF warnings are normal Git line-ending notices, not failed uploads. Unpack the **v0.12.0 source** ZIP, then copy the contents of its `soundThemes` folder (including `manifest.ini`, `globalPlugins/`, `doc/`, `.github/` and this `README.md`) into the **existing** GitHub repository folder. Do not `git init`, clone a second time, re-add `origin` or reuse the old tag.

```powershell
cd D:\NVDA\soundThemes
git pull --ff-only origin main
# Now copy all files from inside the extracted v0.12.0 soundThemes folder here.
git add -A
git -c user.name="Nuttawat Seecham" -c user.email="nutblind2545t@gmail.com" commit -m "Release Sound Themes for NVDA 0.12.0: typing keys and preset removal"
git push origin main
git tag v0.12.0
git push origin v0.12.0
```

On `main` pushes, the included GitHub Actions workflow runs tests and packages a downloadable artifact. Pushing the **new** `v0.12.0` tag creates a separate GitHub Release with the actual `.nvda-addon` installer. The release appears only once its GitHub Actions workflow succeeds. GitHub authentication may be required (e.g. Git Credential Manager). The add-on homepage is provided by `url` in `manifest.ini`, which is the same as the required **homepage** field when publishing to the NVDA Add-on Store. Creating a GitHub repository/release does not automatically add the add-on to NVDA's Store: submit its **direct GitHub Release asset download URL** using the [official NVDA Add-on Store submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md) and complete the review/validation process.

Sources: [navSounds](https://github.com/ahmedthebest31/navsounds), [official navSounds sound store](https://ahmedthebest31.github.io/navsounds/store/), ScreenReaderSounds files provided by the user, [Kliq (MIT; sound recordings by Cris)](https://github.com/crafter-station/kliq), [NVDA developer documentation](https://download.nvaccess.org/documentation/developerGuide.html). See `doc/KLIQ_LICENSE.txt`.
