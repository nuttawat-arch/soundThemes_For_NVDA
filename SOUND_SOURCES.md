# Sound provenance and merger status — v0.17.0 (2026-10-24)

Version 0.17.0 improves sound-queue dispatch and adds a playback report. All previous 1,398 imported original WAV files and their mappings remain intact. Version 0.16.0 changed user-interface wording, keyboard focus navigation and localization.

Version 0.15.0 does not add or remove any supplied audio files. The user reported that `typing/iphone-keyboard` and `typing/voiceover` sound alike. We verified all three matching event WAVs (`key.character`, `key.space`, `key.backspace`) have **different SHA-256 content hashes**, and both sets use different PCM bit depths (iPhone 16-bit, VoiceOver 24-bit). Decoding their typing-character WAVs at 44.1 kHz gives a near-zero sample-to-sample waveform correlation, not matching audio with only different metadata. The sound *style* may be similar, but deleting one would remove distinguishable original recordings. Both remain independently user-editable/deletable and are **not** combined or removed by the release.

Version 0.14.0 imports both the TalkBack and VoiceOver subdirectories of the user-supplied `ScreenReaderSounds(1).zip`, including nested `voiceover/objdata.zip`. Canonical event names are derived from the original filenames, not synthesized; nested original ScreenReaderSounds samples take priority over flat files for duplicate events, and ScreenReaderSounds recordings take priority over older navSounds recordings where the same event is present. The new import adds **43 WAVs** to the previous 1,355. Existing files are retained when the incoming originals are byte-identical. The 26 packaged audio directories are now **editable presets** rather than protected built-ins. Source formats and licenses must still be honored.

Version 0.13.0 extends the seven real Kliq keyboard packs with their individual `*-up.wav` key-release samples, including only source key names matched to Windows keyboard events. The per-pack counts below include up to two actual fixed fallback recordings, each copied verbatim from the **same source pack**. New `keyboard/bucklespring` contains **209 of 209** original `NN-0.wav` and `NN-1.wav` recordings from the user-supplied `bucklespring-master.zip`; all source scan codes are mapped, with `1` for press and `0` for release exactly as in the author's C code. No sounds were generated, resampled or concatenated. Bucklespring (© 2016 Ico Doornekamp) is published under **GNU General Public License version 2**: the full license is distributed with the add-on at `doc/BUCKLESPRING_LICENSE.txt`; upstream project: https://github.com/zevv/bucklespring . Copies/redistributions of these recordings must comply with their license.

Version 0.9.0 imports the new user-provided `upload/effects.zip`: **86 original navSounds/default and 61 original typing WAVs**. The importer retained **85 unique default navigation events** after mapping both editable-text names to one role; an additional **59 missing event recordings** were copied into the existing VoiceOver navigation pack without replacing any original ScreenReaderSounds files. Eleven new typing folders were created, and the existing Classic Typewriter folder gained its real original carriage-bell cue. No synthesized WAVs were used, and duplicate same-event/same-audio variations were omitted. Version 0.8.0 instant audition is preserved.

All **1,398 original WAV assets** reside inside `globalPlugins/soundThemes/effects/`. Editing/renaming/deleting these presets changes the files in the installed add-on. The older external `NVDA user config/soundThemes/effects` directory is **never created by v0.14**: old user packs can be copied from it once during migration, without deleting their source. **Export customized presets as ZIPs before an add-on upgrade, which may overwrite files installed inside the add-on directory.** The obsolete synthetic sound generator remains absent. Runtime playback has up to twelve independent streams with a bounded wait queue; see `FEATURE_AUDIT.md`.

| Editable sound preset | Genuine WAV files | Origin |
|---|---:|---|
| `navigation/voiceover` | **110** | ScreenReaderSounds prioritized, including new supplied VoiceOver cues; genuine older additional navSounds events remain available |
| `navigation/talkback` | **39** | Original TalkBack event WAVs from ScreenReaderSounds(1).zip |
| `navigation/default` | **85** | 86 supplied navSounds/default WAVs, normalized to distinct canonical NVDA events; one duplicate editable-text alias collapsed |
| `typing/classic-typewriter` | **7** | Six official original navSounds character variants plus the user's real Classic Typewriter carriage bell |
| `typing/voiceover` | **4** | Original ScreenReaderSounds typing WAVs |
| `typing/talkback` | **3** | Original TalkBack typing WAVs from ScreenReaderSounds(1).zip |
| `typing/blue-switch` | **3** | Original effects.zip blue switch samples |
| `typing/red-switch` | **3** | Original effects.zip red switch samples |
| `typing/brown-switch` | **7** | Original effects.zip brown switch samples |
| `typing/android-keyboard-1` | **1** | Original effects.zip Android typing sample |
| `typing/android-keyboard-2` | **2** | Original effects.zip Android typing/space samples |
| `typing/iphone-keyboard` | **3** | Original effects.zip iPhone samples |
| `typing/key-1` | **12** | Original effects.zip mechanical typing variations |
| `typing/key-2` | **12** | Original effects.zip mechanical typing variations |
| `typing/perkins-braille` | **2** | Original effects.zip Braille-typewriter samples; duplicate originals omitted |
| `typing/samsung-1` | **3** | Original effects.zip Samsung typing samples |
| `typing/samsung-2` | **3** | Original effects.zip Samsung typing samples |
| `keyboard/voiceover` | **3** | Original ScreenReaderSounds Backspace, End and Shift+Tab WAVs |
| `keyboard/cherry` | **130** | Kliq keydown+keyup originals and two genuine same-pack fallbacks |
| `keyboard/dsa` | **130** | Kliq keydown+keyup originals and two genuine same-pack fallbacks |
| `keyboard/kat` | **130** | Kliq keydown+keyup originals and two genuine same-pack fallbacks |
| `keyboard/mt3` | **111** | Kliq originals; five source keyup samples unavailable in this set |
| `keyboard/oem` | **130** | Kliq keydown+keyup originals and two genuine same-pack fallbacks |
| `keyboard/sa` | **126** | Kliq originals; two source keyup samples unavailable in this set |
| `keyboard/xda` | **130** | Kliq keydown+keyup originals and two genuine same-pack fallbacks |
| `keyboard/bucklespring` | **209** | All source Bucklespring recordings (GPL v2) |
| **Total** | **1,398** | **Real audio only; 26 fully editable packs including 8 switch-keyboard themes** |

Reimport the new complete ScreenReaderSounds split archive:

```bash
python soundThemes/scripts/import_screenreader_multitheme.py 'upload/ScreenReaderSounds(1).zip'
```

The importer detects VoiceOver and TalkBack separately, resolves canonical event aliases, prefers `voiceover/objdata.zip` on duplicate event names and retains original audio byte content when already in WAV format. Non-PCM audio is converted **offline**, never synthesized. It updates the navigation and typing folders; keyboard pack keydown/keyup recordings are unchanged.

For deterministic re-import when `effects.zip` is supplied next to the project:

```bash
python soundThemes/scripts/import_effects_archive.py upload/effects.zip
```

This importer validates each original PCM WAV, fixes the spelling errors `expended`, `invisibled`, `tablecoulmnheader`, `tableraw`, and maps focus/caret/status names to the right canonical events. It preserves actual byte content and original ScreenReaderSounds priority. Some historical role names in the supplied archive may no longer exist as modern NVDA `controlTypes.Role` members; only actual NVDA focus/state callbacks can play those recordings. Having a WAV available is not proof that Windows will report that event. The source ZIP contains the *importer* and the installed selected audio; it does not contain the redundant source archive.

Unlike the previous code-only archive, `upload/ScreenReaderSounds.zip` now has **55 entries, about 17 MB**: 50 top-level WAVs, `objdata.zip` with another 24 genuine role WAVs, and three original OGG sounds (`ready.ogg`, `tick.ogg`, `volume_beep.ogg`). The audio importer converted the OGG files **offline** to PCM WAV using ffmpeg, not synthesized sound. It placed **54 distinct canonical event assignments** in navigation/typing/keyboard folders; on duplicate role names the distinct files inside `objdata.zip` win over top-level role WAVs, many of which share duplicate content. Identical event names are deduplicated; different named events remain separate even if original bytes repeat.

`upload/navSounds.zip` was code only. Official sound downloads supplied the genuine first 21 assets:

- [Voiceover original](https://ahmedthebest31.github.io/navsounds/store/packs/voiceover/voiceover.zip) SHA-256 `1b18726664503a73089583f760b05eb5274bdcefcaaf57f063b6855d6ee793df`.
- [Classic Typewriter original](https://ahmedthebest31.github.io/navsounds/store/packs/classic-typewriter/classic-typewriter.zip) SHA-256 `26ae1d93a5cd4920eacbac0a3e7c4f44cf77d87c3ec58c4f852512fec6127aa7`.

Reimport actual original audio:

```bash
python soundThemes/scripts/import_original_audio.py --screenreader-addon upload/ScreenReaderSounds.zip
```

The earlier importer also recognizes audio-bearing ScreenReaderSounds installers with VoiceOver or TalkBack trees. The new multi-theme importer above includes a TalkBack pack. The Mechvibes long-OGG format is **not included**.

The user supplied `upload/Sounds.zip` containing the Kliq per-key audio. Official project: https://github.com/crafter-station/kliq (MIT, Copyright 2026 Crafter Station; audio design by Cris). The source copyright and full license are included in `doc/KLIQ_LICENSE.txt`. Importer `scripts/import_kliq_audio.py` maps IBM PC set-1 codes to canonical keyboard events and copies **both original `-down.wav` and `-up.wav`** when present. The 7 packs may lack recordings for some keys; each contains a fixed **real same-pack fallback** for press and, when available, release. Nothing is synthesized or randomly selected. A real `click.wav` supplies optional `nav.mouse.wav`.

```bash
python soundThemes/scripts/import_kliq_audio.py upload/Sounds.zip
python soundThemes/scripts/import_bucklespring_audio.py upload/bucklespring-master.zip
```

Audio responsiveness also depends on the callback path: v0.6 corrected Explorer list-item sound mapping and noisy event callbacks; v0.7 replaces the former single interrupting stream with bounded concurrent playback. **These changes still require NVDA 2026 on Windows for real playback validation.**

Assignability does not imply every legacy event can be detected on current NVDA. Speech pause now uses NVDA's public `post_speechPaused` callback. Long click, tutorial activation, volume feedback, and hardware Fn/brightness events still need additional supported callbacks or direct Windows testing. Do not claim full runtime parity from these files alone. Check audio reuse licenses with publishers before wide redistribution.
