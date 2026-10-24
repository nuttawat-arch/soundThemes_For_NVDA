# Sound Themes for NVDA — Keyboard Sounds (v0.15.0)

Open the Sound Themes settings directly from **NVDA menu → Tools → Sound Themes settings...**; it no longer appears as a page inside NVDA's global Settings dialog. Under that standalone window, **Check for updates now** uses official GitHub Releases without needing to submit to the Add-on Store. The local developer-only `release.ps1` automates creating future tagged releases but is never included in the add-on or source ZIP.

Version 0.14.0: NVDA's supported `inputCore.decide_handleRawKey` callback supplies physical **press and release** transitions (`pressed=True`/`False`). The add-on uses it without installing another global keyboard hook or intercepting Windows/NVDA shortcuts. Choose one of **two per-preset** Keyboard playback modes in Manage sound themes → Keyboard Sounds:

1. **Two layers, separate press/release:** `keyboard.a.wav` when pressed and `keyboard.a__release.wav` when released. An auto-repeating held key does not retrigger either sample.
2. **One layer, combined press+release:** one `keyboard.a.wav` plays only on the first keydown. Keyup is always silent; the release already in the same WAV is never duplicated. An old `press` mode is migrated here.

Modes are stored independently for each keyboard preset in normal NVDA configuration. Keyboard ZIP export/import preserves them. All seven Kliq themes include their `*-up.wav` releases; Bucklespring provides 209 genuine samples (`NN-1.wav` = press, `NN-0.wav` = release). All packs are editable and removable. **Because WAVs now live inside the installed add-on rather than in a separate NVDA user-config sound folder, export any edited preset to ZIP before replacing/upgrading the add-on; an NVDA add-on update can replace its files.** The prior external sound folder is only read during one-time migration; it is not recreated. Navigation and Typing remain separate from these keyboard playback modes.

Version 0.12.0: Navigation Sounds now follow web Browse Mode **virtual** cursor movements through links, buttons and headings rather than depending solely on Windows keyboard focus. In a browser, single-letter quick navigation (such as B/K/H) and arrow movement play the role-specific WAV in your chosen navigation pack when NVDA identifies that element. This is independent of physical Keyboard Sounds, which remains off by default. Normal keypress events and browser shortcuts are not intercepted.

Version 0.11.0: **Typing Sounds** can play Enter, Space and Backspace/Delete on physical keydown in editable fields when NVDA omits the typed-character event; duplicate notifications are suppressed. A dedicated event recording is preferred to the pack's real `key.character.wav` fallback. This is distinct from the physical **Keyboard Sounds** category. All presets can be edited, renamed, and deleted directly. The obsolete **Import old sounds folder** button is gone; import theme ZIPs or edit events directly.

Version 0.10.0 fixes a separate cause of the Shift double-sound: NVDA fires `post_speechPaused` when Shift pauses speech. Previous builds played `system.paused_feedback` in addition to the keyboard key sound, even with Navigation disabled. That speech cue is now off by default and always suppressed around a physical Shift press. It can be enabled for other speech-pause events using the independent **Play speech-pause feedback** checkbox. In the editor, each sound event has a screen-reader-readable explanation of its NVDA trigger and typical app context. Its short item label (for example `C`, `Shift`, `LISTITEM`) stays searchable with first-letter navigation.

Version 0.9.0: Windows sometimes exposes both a generic modifier key (such as VK_SHIFT) and its left/right form for the same physical press. The handler now normalizes them to one pressed key and one assigned WAV. This is particularly important for Shift, Control and Alt; it does not disable other keys or the ability to hold two physical modifiers together. If Shift still produces an extra sound, turn off independent keyboard/audio add-ons and Windows Sticky Keys notifications to isolate whether that sound is produced outside Sound Themes.

New in 0.8.0: arrow through a keyboard theme (for example Cherry or KAT) in the settings choice or manager list to hear its representative recording instantly, without changing the active theme. The list says `Cherry`, not `Built-in: Cherry`, so typing `C` jumps to it. In the keyboard event editor, moving the selection auditions the current event; names `A` to `Z` and `0` to `9` start with those actual characters. Previews are decoded in the background and obsolete pending previews are discarded when navigating quickly. This does not change fixed, non-random in-game keyboard cues.

## Three sound categories

| Mode | Default | Trigger | Theme folder |
|---|---|---|---|
| Navigation Sounds | On | Actual NVDA focus, role, state, browse/caret/selection and navigation activity | `effects/navigation/<pack>` |
| Typing Sounds | On | Characters typed in NVDA; random sounds only from the *chosen typing pack* | `effects/typing/<pack>` |
| Keyboard Sounds | Off | First physical key down and optionally the matching keyup via NVDA's raw-key hook | `effects/keyboard/<pack>` |

Enabling **Keyboard Sounds** disables **both** Navigation Sounds and Typing Sounds. Enabling either Navigation or Typing disables Keyboard Sounds. System lock/unlock sounds remain under the independent **System** option.

When Keyboard Sounds is **off**, merely pressing Tab, Shift+Tab, arrows, Home, End or Page Up/Down never triggers a keyboard-key sample. Navigation may still play role/focus/browse/scroll sounds **if NVDA reports actual movement**. Pressing such a key without a resulting movement is silent.

## Keyboard sound packs: press and optional release per key

Every pack contains real uncompressed PCM `.wav` recordings. **No `theme.json`** or timed `sound.ogg` sprites are needed. Each press/release phase plays **at most one** file, with no randomness. `keyboard.default.wav` can cover an unrecorded press, while `keyboard.default__release.wav` can cover an unrecorded release. A release never borrows a press WAV; fallbacks are always from the same pack.

Examples:

```text
globalPlugins/soundThemes/effects/
    navigation/voiceover/role.button.wav
    navigation/talkback/role.button.wav
    typing/classic-typewriter/key.character__original.wav
    typing/talkback/key.character.wav
    keyboard/voiceover/keyboard.shift_tab.wav
    keyboard/My-Keyboard/keyboard.a.wav
    keyboard/My-Keyboard/keyboard.a__release.wav
    keyboard/My-Keyboard/keyboard.left_ctrl.wav
    keyboard/My-Keyboard/keyboard.f12.wav
    keyboard/kat/keyboard.default.wav
```

The built-in `keyboard/voiceover` pack retains **three real ScreenReaderSounds files** (Backspace, End, Shift+Tab). Seven Kliq switch themes are Cherry, DSA, KAT, MT3, OEM, SA and XDA (KAT remains the first-install default). Original Kliq down/up scan codes are mapped to distinct `keyboard.<key>.wav` and `keyboard.<key>__release.wav` files without altering the sound. The eighth switch theme, Bucklespring, includes its 209 real recordings. A theme can provide fixed, genuine press/release fallback recordings; missing keys without corresponding fallbacks remain silent.

The Windows virtual-key catalog includes 1–255, A–Z, 0–9, punctuation, left/right modifiers, Caps Lock, Num Lock, Tab, Escape, Space, Enter, arrows, Home/End, Page Up/Down, F1–F24, numpad, browser/media/volume keys and unknown codes. The editor also offers extra keys such as Dim Screen/Brightness Up and Fn. **Hardware Fn or brightness buttons that do not emit Windows keyboard events cannot be detected by NVDA's raw-key extension; listing them as assignable does not guarantee they can trigger on every computer.**

## How to use the editor without a mouse

1. Open NVDA → Tools → Sound Themes settings...
2. Choose **Manage sound themes** (only one main management button).
3. Use the notebook tabs: **Navigation**, **Typing**, **Keyboard Sounds**. Select the keyboard tab.
4. Select any theme and choose **Edit sounds**, **Rename**, or **Delete** directly. There are no protected built-in themes. Create or copy a pack only if you want another one.
5. The editor shows **one alphabetical event list**, without category/group dropdowns. Its items have familiar short names such as `checkbox`, `text`, `A`, and `Shift`. Alternatively, Tab to **Capture and preview a physical key** and press the exact key. Capture operates only while its field has focus; `Esc` inside capture is a key assignment.
6. Choose **Replace WAV** for a press/combined sample, or **Replace key release WAV** for a separate release click. The editor saves them as `keyboard.f7.wav` and `keyboard.f7__release.wav`, regardless of source filename. Separate Preview and Remove controls are provided for the release. **No random variations** are allowed in keyboard themes.
7. Choose **Done** to save edits or **Cancel** to revert edits made in that editor session, including WAV removal/replacement. **Use this theme**, close the manager, choose it in **Keyboard sound theme** and tick **Keyboard Sounds**. The **Open sound folders** button opens the add-on's embedded `effects` directory, containing all three sound categories.

Source pack import also recognizes canonical `keyboard.a.wav`, `a.wav`, `KeyA.wav`, `Digit1.wav`, `ShiftLeft.wav`, `ArrowUp.wav` and similar unambiguous filenames. Ambiguous filenames are **not randomly assigned**: choose their intended key in the editor instead.

## Where to get real *individual key* WAVs

- Official Mechvibes sound packs: https://mechvibes.com/sound-packs/ . **Check inside the ZIP before importing.** Many Mechvibes / MechvibesDX packs contain one long `sound.ogg` with `config.json` timing offsets, which is *not* directly compatible with Sound Themes' one-file-per-key model.
- MechvibesDX official format document: https://github.com/hainguyents13/mechvibes-dx/blob/main/docs/soundpack-config-v2.md — the `multi` definition method permits one independent sound file per key; the usual `single` method uses time-sliced audio.
- **Kliq keyboard sound library (GitHub):** https://github.com/crafter-station/kliq . Its source contains seven sets of real per-key `-down.wav` / `-up.wav` recordings. The supplied archive has fewer recorded F-key samples than the format supports; a fixed in-pack fallback plays those keys. The included importer maps scan codes to names automatically. Kliq is MIT licensed; the complete copyright/license notice accompanies the add-on.

Important: The user-supplied `Sounds.zip` from Kliq is included as **seven keydown+keyup themes**. The supplied `bucklespring-master.zip` has its own distinct preset; its author distributes it under GNU GPL v2 (license included). A full automatic importer for long, timed OGG Mechvibes packs is deliberately not part of the NVDA runtime.

## Original ScreenReaderSounds files

The original `ScreenReaderSounds.zip` supplied **54 distinct mapped events**, including three physical keyboard events; three OGGs were decoded to PCM WAV. The newer `ScreenReaderSounds(1).zip` additionally supplies genuine VoiceOver and TalkBack packs. ScreenReaderSounds wins when its canonical event overlaps with NavigationSounds. Version 0.14 ships **1,398 genuine WAVs across 26 editable packs**, including TalkBack navigation and typing. Bare legacy sound names such as `checkbox.wav` and `editabletext.wav` are accepted, and the editor displays concise event labels without `System` prefixes. Some uncommon NVDA/hardware events still require live Windows testing.
