# Sound Themes for NVDA 0.7.0

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

Open NVDA menu → Preferences → Settings → **Sound Themes**. Select three active theme packs. The single **Manage sound themes...** button opens a dialog with **Navigation**, **Typing** and **Keyboard Sounds** tabs. Each has Create/Copy, Edit, Rename, Delete, Import ZIP, Import WAV folder, Export ZIP and Use This Theme. Built-in packs are read-only; edit first creates a personal copy. The single **Open sound folders** button opens the NVDA user effects root.

In the keyboard editor, navigate to **Capture and preview a physical key**. Press any accessible key: the editor selects that physical-key event and immediately previews its assigned WAV. Outside the capture field, Tab/Escape still navigate normally. Select **Replace WAV** to choose a file from anywhere, regardless of filename; the editor saves it as `keyboard.a.wav`, `keyboard.f7.wav`, etc. There is no random-variation button for keyboard packs. Kliq packs have a genuine in-pack fallback sample for keys not individually recorded; custom packs without a fallback remain silent on missing bindings.

Read [KEYBOARD_SOUNDS_GUIDE.md](KEYBOARD_SOUNDS_GUIDE.md) for full details, examples, and verified download links.

## Sound storage

```text
globalPlugins/soundThemes/effects/
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

The audio-bearing 17 MB `upload/ScreenReaderSounds.zip` contains 50 top-level WAVs, another 24 WAVs inside `objdata.zip`, plus three original OGG recordings. Its source produced **54 unique canonical event assignments**, with inner role recordings taking precedence on duplicates and original OGG recordings decoded offline to real PCM WAVs. Combining both original NVDA add-ons and the **seven real Kliq keyboard sets** from `upload/Sounds.zip` produces **510 genuine WAV files** across 11 built-in sound folders, without synthesized audio. The Kliq importer intentionally omits unused key-release files. See [SOUND_SOURCES.md](SOUND_SOURCES.md) and [FEATURE_AUDIT.md](FEATURE_AUDIT.md).

**Seven built-in keyboard themes** are now available: Cherry, DSA, KAT (new-install default), MT3, OEM, SA and XDA. Every recorded key maps directly from its original scan code to one canonical WAV; a missing key uses the same pack's fixed, genuine `keyboard.default.wav` (no randomness or mixing packs). The additional original `keyboard/voiceover` theme remains available. Hardware-specific Fn/brightness buttons may not emit Windows keyboard events visible to NVDA. Some legacy ScreenReaderSounds event IDs are stored for later support but are not yet wired to dependable runtime triggers.

Explorer item navigation prioritizes the real `role.listitem`/`role.treeviewitem` sample over unavailable `state.selected`. **Version 0.7 plays up to twelve sounds concurrently**, through independent reusable NVDA WASAPI players. Long navigation WAVs no longer stop or block another navigation or typing sample. The audio queue is bounded, discarding superseded *pending* cues only when the streams are busy; there is no unbounded playback backlog. This change also applies to Keyboard Sounds when that mode is enabled. The existing rule that Keyboard Sounds disables Navigation and Typing remains intact. Test live responsiveness on Windows NVDA before considering it production-verified.

## Build, test and install

```bash
python -B -m unittest discover -s tests -v
python scripts/build.py
python scripts/build_source.py
```

Run these commands **from the `soundThemes` source directory**. To reimport the optional original supplied archive, run `python scripts/import_kliq_audio.py ../upload/Sounds.zip` if that archive is present. Install `SoundThemesForNVDA-0.7.0.nvda-addon` using NVDA's add-on manager, restart NVDA, and disable old navSounds/ScreenReaderSounds to avoid duplicate feedback. For an existing configuration, select KAT or another Kliq theme under Keyboard Sounds; existing choice `voiceover` is not overwritten. Try portable NVDA 2026 first: static Python tests outside Windows do **not** prove hardware event delivery, secure-desktop playback or accessible Windows wx dialogs.

## Publishing to GitHub and the NVDA Add-on Store

The repository above is public and currently empty. Unpack the **source** ZIP, then copy the contents of its `soundThemes` folder (including `manifest.ini`, `globalPlugins/`, `doc/`, `.github/` and this `README.md`) into a fresh clone of the repository. Do **not** use `echo "# ..." >> README.md`: this README already exists.

```bash
git clone https://github.com/nuttawat-arch/soundThemes_For_NVDA.git
cd soundThemes_For_NVDA
# Copy all source files, including hidden .github and .gitignore, here first.
git add -A
git -c user.name="Nuttawat Seecham" -c user.email="nutblind2545t@gmail.com" commit -m "Release Sound Themes for NVDA 0.7.0"
git push -u origin main
git tag v0.7.0
git push origin v0.7.0
```

On `main` pushes, the included GitHub Actions workflow runs the tests and packages a downloadable build artifact. Pushing `v0.7.0` also creates a GitHub Release with the actual `.nvda-addon` installer. GitHub authentication may be required (e.g. Git Credential Manager or `gh auth login`). The add-on homepage is provided by `url` in `manifest.ini`, which is the same as the required **homepage** field when publishing to the NVDA Add-on Store. Creating a GitHub repository/release does not automatically add the add-on to NVDA's Store: submit its **direct GitHub Release asset download URL** using the [official NVDA Add-on Store submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md) and complete the review/validation process.

Sources: [navSounds](https://github.com/ahmedthebest31/navsounds), [official navSounds sound store](https://ahmedthebest31.github.io/navsounds/store/), ScreenReaderSounds files provided by the user, [Kliq (MIT; sound recordings by Cris)](https://github.com/crafter-station/kliq), [NVDA developer documentation](https://download.nvaccess.org/documentation/developerGuide.html). See `doc/KLIQ_LICENSE.txt`.
