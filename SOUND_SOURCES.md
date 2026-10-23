# Sound provenance and merger status — v0.8.0 (2026-10-24)

Version 0.8.0 adds automatic theme/event audition using the very same real WAV files listed below; it neither synthesizes new samples nor changes pack identities. Keyboard previews prefer that pack's original `keyboard.a.wav`, falling back to an available file in the *same* pack.

All **510 original recordings** now reside in the single packaged directory `globalPlugins/soundThemes/effects/`; the old extra `globalPlugins/Sound Themes for NVDA/` asset directory is no longer used. No sound recording was deleted by the move, and no synthesized sound generator is included in source or installer. Runtime playback has up to twelve independent streams with a bounded wait queue; see `FEATURE_AUDIT.md`.

| Built-in sound folder | Genuine WAV files | Origin |
|---|---:|---|
| `navigation/voiceover` | **50** | Original navSounds Voiceover plus ScreenReaderSounds WAVs; SRS role sound priority. One Kliq `click.wav` mapped to optional mouse hover. |
| `typing/classic-typewriter` | **6** | Official original navSounds Classic Typewriter, six variants of the *same* character event |
| `typing/voiceover` | **4** | Original ScreenReaderSounds typing WAVs |
| `keyboard/voiceover` | **3** | Original ScreenReaderSounds Backspace, End and Shift+Tab WAVs |
| `keyboard/cherry` | **65** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/dsa` | **65** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/kat` | **65** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/mt3` | **58** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/oem` | **65** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/sa` | **64** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| `keyboard/xda` | **65** | Kliq genuine key-down WAVs, one genuine in-pack fallback |
| **Total** | **510** | **Real audio only; 7 Kliq packs** |

Unlike the previous code-only archive, `upload/ScreenReaderSounds.zip` now has **55 entries, about 17 MB**: 50 top-level WAVs, `objdata.zip` with another 24 genuine role WAVs, and three original OGG sounds (`ready.ogg`, `tick.ogg`, `volume_beep.ogg`). The audio importer converted the OGG files **offline** to PCM WAV using ffmpeg, not synthesized sound. It placed **54 distinct canonical event assignments** in navigation/typing/keyboard folders; on duplicate role names the distinct files inside `objdata.zip` win over top-level role WAVs, many of which share duplicate content. Identical event names are deduplicated; different named events remain separate even if original bytes repeat.

`upload/navSounds.zip` was code only. Official sound downloads supplied the genuine first 21 assets:

- [Voiceover original](https://ahmedthebest31.github.io/navsounds/store/packs/voiceover/voiceover.zip) SHA-256 `1b18726664503a73089583f760b05eb5274bdcefcaaf57f063b6855d6ee793df`.
- [Classic Typewriter original](https://ahmedthebest31.github.io/navsounds/store/packs/classic-typewriter/classic-typewriter.zip) SHA-256 `26ae1d93a5cd4920eacbac0a3e7c4f44cf77d87c3ec58c4f852512fec6127aa7`.

Reimport actual original audio:

```bash
python soundThemes/scripts/import_original_audio.py --screenreader-addon upload/ScreenReaderSounds.zip
```

The same importer also recognizes audio-bearing ScreenReaderSounds installers with separate VoiceOver, TalkBack 5, or TalkBack 6 audio trees, if they are supplied later. Such complete TalkBack packs are **not yet included**. The Mechvibes long-OGG format is also **not included**.

The user supplied `upload/Sounds.zip` containing the Kliq per-key audio. Official project: https://github.com/crafter-station/kliq (MIT, Copyright 2026 Crafter Station; audio design by Cris). The source copyright and full license are included in `doc/KLIQ_LICENSE.txt`. Importer `scripts/import_kliq_audio.py` maps IBM PC set-1 codes to canonical keyboard events and copies **only key-down WAVs**, omitting every unused `-up.wav`. Of the 7 packs, a few lack recordings for some keys, which is why each pack contains the **real space-bar recording** as `keyboard.default.wav` (never synthesized or random). A real original `click.wav` supplies optional `nav.mouse.wav`.

```bash
python soundThemes/scripts/import_kliq_audio.py upload/Sounds.zip
```

Audio responsiveness also depends on the callback path: v0.6 corrected Explorer list-item sound mapping and noisy event callbacks; v0.7 replaces the former single interrupting stream with bounded concurrent playback. **These changes still require NVDA 2026 on Windows for real playback validation.**

Assignability does not imply every legacy event can be detected on current NVDA. Speech pause now uses NVDA's public `post_speechPaused` callback. Long click, tutorial activation, volume feedback, and hardware Fn/brightness events still need additional supported callbacks or direct Windows testing. Do not claim full runtime parity from these files alone. Check audio reuse licenses with publishers before wide redistribution.
