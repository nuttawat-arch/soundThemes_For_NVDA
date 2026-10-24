# NVDA add-on dependencies and Sound Themes audio backend

## What is already used

Sound Themes plays PCM WAVs with NVDA's built-in `nvwave.WavePlayer`, which uses
NVDA's WASAPI integration and selected output device. Python packages used in
the installed add-on are from NVDA's own modules and normal bundled runtime;
there is no separate `pip install` step for Sound Themes.

This is a deliberate stability choice. The add-on currently requires playback
of short WAV event cues, not music decoding or 3D sound. `nvwave` already
supports independent streams and avoids introducing another native audio
device stack. We are retaining it in the v0.17 candidate while testing the
actual cause of occasional missing or surprising sounds.

## How third-party Python dependencies work in an NVDA add-on

The official NVDA developer guide warns that NVDA's own pip packages may
change independently of add-ons. An add-on should **bundle** the exact
compatible dependencies it needs, rather than assume they are available in
the user's installed NVDA or Windows Python. A `requirements.txt` file by
itself does **not** make NVDA automatically install packages when someone
opens a `.nvda-addon` file.

If a future feature really needs a new library:

1. Select a maintained package and version, audit its license and transitively
   required packages, and verify its Python version and Windows CPU
   architecture against the supported NVDA releases.
2. Install it in a **separate build environment** only. Copy the required
   package, data files, notices, and permitted native DLLs into a dedicated
   package within the add-on source. Avoid modifications to NVDA's program
   folder, system Python, or globally installed libraries.
3. Import it from the add-on's own namespace, ensuring any internal absolute
   imports and native DLL lookup paths work in NVDA. Catch optional import
   failure without preventing NVDA's global plugin from starting. The `.pyd`
   extension ABI must match NVDA's embedded Python.
4. Include the files in the `.nvda-addon` installer and source ZIP. The
   project's `scripts/build.py` includes the `globalPlugins` tree; confirm
   every dependency and attribution file is packaged and can be removed
   cleanly with the add-on.
5. Test a fresh portable NVDA in Windows, NVDA upgrade behavior, audio-device
   switching, multiple themes, rapid typing, screen-reader speech, unplugged
   devices, plugin removal/reinstallation and the required license notices.

Do **not** run pip from `installTasks.py`, silently download executable
dependencies on NVDA startup, or copy DLLs into the main NVDA installation.
The install task hook is intended for narrow install/uninstall work and should
load as few modules as possible.

## Sound_lib / BASS evaluation

The community `sound_lib` Python package wraps the BASS multimedia engine.
It provides additional playback formats, effects and stream APIs, which could
be useful in a **future** release. It is not automatically superior for the
existing short PCM WAV event effects. BASS introduces separate Windows DLLs,
an extra audio-device lifecycle and licensing conditions; BASS is free only
for qualifying non-commercial use. Sound_lib's Python wrapper is MIT, but
that does not remove BASS's independent license requirements.

Do not make BASS a compulsory dependency or silently replace `nvwave` until
a Windows NVDA acceptance test and distribution/license review are complete.
An eventual implementation should live behind a backend interface and fall
back to `nvwave` when its optional dependency is unavailable.

## References

- [NVDA 2026.2 developer guide — add-on API, dependencies and packaging](https://api.nvaccess.org/releases/2026.2beta7/documentation/developerGuide.html)
- [NVDA `nvwave.py` implementation](https://github.com/nvaccess/nvda/blob/master/source/nvwave.py)
- [Accessible Apps sound_lib source](https://github.com/accessibleapps/sound_lib)
- [Un4seen BASS licensing](https://www.un4seen.com/bass.html)

This document describes code and packaging policy, not an additional user
setting or a requirement to install third-party software.
