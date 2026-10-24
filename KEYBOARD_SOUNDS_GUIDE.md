# Sound Themes for NVDA — Keyboard Sounds (v0.12.0)

Version 0.12.0: Navigation Sounds now follow web Browse Mode **virtual** cursor movements through links, buttons and headings rather than depending solely on Windows keyboard focus. In a browser, single-letter quick navigation (such as B/K/H) and arrow movement play the role-specific WAV in your chosen navigation pack when NVDA identifies that element. This is independent of physical Keyboard Sounds, which remains off by default. Normal keypress events and browser shortcuts are not intercepted.

Version 0.11.0: **Typing Sounds** can now play Enter, Space and Backspace/Delete on a physical keydown in focused editable fields even when NVDA does not emit a typed-character notification. Matching later notifications are suppressed to avoid doubling. Dedicated samples such as `key.enter.wav` are preferred; otherwise the pack's genuine `key.character.wav` is used (no synthetic audio and no mixing themes). This is Typing Sounds behavior, not the physical **Keyboard Sounds** category, which has its own `keyboard.enter.wav` and similar key events. All categories allow removal of every listed preset; built-in removal is persistent and reversible using **Restore removed presets**. The obsolete **Import old sounds folder** button is gone; import theme ZIPs or edit WAV events directly.

Version 0.10.0 fixes a separate cause of the Shift double-sound: NVDA fires `post_speechPaused` when Shift pauses speech. Previous builds played `system.paused_feedback` in addition to the keyboard key sound, even with Navigation disabled. That speech cue is now off by default and always suppressed around a physical Shift press. It can be enabled for other speech-pause events using the independent **Play speech-pause feedback** checkbox. In the editor, each sound event has a screen-reader-readable explanation of its NVDA trigger and typical app context. Its short item label (for example `C`, `Shift`, `LISTITEM`) stays searchable with first-letter navigation.

Version 0.9.0: Windows sometimes exposes both a generic modifier key (such as VK_SHIFT) and its left/right form for the same physical press. The handler now normalizes them to one pressed key and one assigned WAV. This is particularly important for Shift, Control and Alt; it does not disable other keys or the ability to hold two physical modifiers together. If Shift still produces an extra sound, turn off independent keyboard/audio add-ons and Windows Sticky Keys notifications to isolate whether that sound is produced outside Sound Themes.

New in 0.8.0: arrow through a keyboard theme (for example Cherry or KAT) in the settings choice or manager list to hear its representative recording instantly, without changing the active theme. The list says `Cherry`, not `Built-in: Cherry`, so typing `C` jumps to it. In the keyboard event editor, moving the selection auditions the current event; names `A` to `Z` and `0` to `9` start with those actual characters. Previews are decoded in the background and obsolete pending previews are discarded when navigating quickly. This does not change fixed, non-random in-game keyboard cues.

## Three sound categories

| Mode | Default | Trigger | Theme folder |
|---|---|---|---|
| Navigation Sounds | On | Actual NVDA focus, role, state, browse/caret/selection and navigation activity | `effects/navigation/<pack>` |
| Typing Sounds | On | Characters typed in NVDA; random sounds only from the *chosen typing pack* | `effects/typing/<pack>` |
| Keyboard Sounds | Off | Each physical key **down** delivered by NVDA's raw-key hook | `effects/keyboard/<pack>` |

Enabling **Keyboard Sounds** disables **both** Navigation Sounds and Typing Sounds. Enabling either Navigation or Typing disables Keyboard Sounds. System lock/unlock sounds remain under the independent **System** option.

When Keyboard Sounds is **off**, merely pressing Tab, Shift+Tab, arrows, Home, End or Page Up/Down never triggers a keyboard-key sample. Navigation may still play role/focus/browse/scroll sounds **if NVDA reports actual movement**. Pressing such a key without a resulting movement is silent.

## Keyboard sound packs: one file per key

Every pack is a directory of real, uncompressed PCM `.wav` recordings. **No `theme.json`** and no timed `sound.ogg` sprite are needed. A keyboard event plays **exactly one assigned file**; no random choice. A missing event is silent unless that pack contains the genuine `keyboard.default.wav` fallback. The fallback is always from the same pack, never an artificial effect or a sample from another pack.

Examples:

```text
globalPlugins/soundThemes/effects/
    navigation/voiceover/role.button.wav
    typing/classic-typewriter/key.character__original.wav
    keyboard/voiceover/keyboard.shift_tab.wav

NVDA user config/soundThemes/effects/
    navigation/My-Navigation/role.button.wav
    typing/My-Typing/key.character.wav
    keyboard/My-Keyboard/keyboard.a.wav
    keyboard/My-Keyboard/keyboard.left_ctrl.wav
    keyboard/My-Keyboard/keyboard.f12.wav
    keyboard/My-Keyboard/keyboard.pageup.wav
    keyboard/My-Keyboard/keyboard.brightness_down.wav
    keyboard/kat/keyboard.default.wav
```

The built-in `keyboard/voiceover` pack still contains **three real ScreenReaderSounds files** (Backspace, End, Shift+Tab). Seven additional keyboard themes contain genuine Kliq audio supplied by the user: Cherry, DSA, KAT, MT3, OEM, SA and XDA. KAT is the default for new installations. The original Kliq key-down scan codes are renamed to `keyboard.<key>.wav` without changing the recorded audio. The included seven packs each have a fixed real space-bar WAV as `keyboard.default.wav` for buttons not separately recorded (e.g. some function/media keys). There is no generated placeholder audio. For a custom pack, remove/replace `keyboard.default.wav` if you want unmatched keys to be silent or use a different real recording.

The Windows virtual-key catalog includes 1–255, A–Z, 0–9, punctuation, left/right modifiers, Caps Lock, Num Lock, Tab, Escape, Space, Enter, arrows, Home/End, Page Up/Down, F1–F24, numpad, browser/media/volume keys and unknown codes. The editor also offers extra keys such as Dim Screen/Brightness Up and Fn. **Hardware Fn or brightness buttons that do not emit Windows keyboard events cannot be detected by NVDA's raw-key extension; listing them as assignable does not guarantee they can trigger on every computer.**

## How to use the editor without a mouse

1. Open NVDA → Preferences → Settings → Sound Themes.
2. Choose **Manage sound themes** (only one main management button).
3. Use the notebook tabs: **Navigation**, **Typing**, **Keyboard Sounds**. Select the keyboard tab.
4. Choose **Create / copy selected**, name a new theme and select **Edit sounds**. Built-in themes are read-only; editing them first creates a personal copy.
5. In the keyboard editor, select an event from its group/list; alternatively, Tab to **Capture and preview a physical key** and press the exact key to choose and hear its assigned WAV. Capture acts only while that field has focus; other controls keep ordinary keyboard navigation. `Esc` in capture is a key assignment, not dialog cancel.
6. Choose **Replace WAV**, browse to *any* existing PCM WAV (its original filename can be anything) and open it. The editor stores it under the selected event ID, e.g. selecting F7 turns `my_click_23.wav` into `keyboard.f7.wav`. **No random variations are allowed in keyboard themes.** Use **Preview** to listen. Repeat for other keys.
7. **Use this theme**, close the manager, choose it in **Keyboard sound theme** and tick **Keyboard Sounds**. Navigation and Typing are switched off; save the page. The single **Open sound folders** button opens the parent containing all three user categories.

Source pack import also recognizes canonical `keyboard.a.wav`, `a.wav`, `KeyA.wav`, `Digit1.wav`, `ShiftLeft.wav`, `ArrowUp.wav` and similar unambiguous filenames. Ambiguous filenames are **not randomly assigned**: choose their intended key in the editor instead.

## Where to get real *individual key* WAVs

- Official Mechvibes sound packs: https://mechvibes.com/sound-packs/ . **Check inside the ZIP before importing.** Many Mechvibes / MechvibesDX packs contain one long `sound.ogg` with `config.json` timing offsets, which is *not* directly compatible with Sound Themes' one-file-per-key model.
- MechvibesDX official format document: https://github.com/hainguyents13/mechvibes-dx/blob/main/docs/soundpack-config-v2.md — the `multi` definition method permits one independent sound file per key; the usual `single` method uses time-sliced audio.
- **Kliq keyboard sound library (GitHub):** https://github.com/crafter-station/kliq . Its source contains seven sets of real per-key `-down.wav` / `-up.wav` recordings. The supplied archive has fewer recorded F-key samples than the format supports; a fixed in-pack fallback plays those keys. The included importer maps scan codes to names automatically. Kliq is MIT licensed; the complete copyright/license notice accompanies the add-on.

Important: The user-supplied `Sounds.zip` from Kliq **is now included in the release as seven key-down-only themes**. The `-up.wav` files and standalone samples unused by the active playback mode are not packaged. A full automatic importer for long, timed OGG Mechvibes packs is deliberately not part of the NVDA runtime.

## Original ScreenReaderSounds files

The user-provided `ScreenReaderSounds.zip` was read in v0.5.0: original WAVs at the archive root, distinct role sounds in nested `objdata.zip`, and three actual OGG recordings. It yielded **54 distinct mapped events, including three separate keyboard events**; original OGGs were decoded offline into PCM WAV (not fabricated). Duplicate roles prefer the inner `objdata` recording. Version 0.9.0 also imports the user's new `effects.zip` WAVs for missing navigation events and typing packs: **706 real WAVs total** in the add-on, including the seven genuine Kliq per-key switch sets. Some uncommon NVDA/hardware events still require Windows testing.
