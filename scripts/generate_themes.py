"""Generate original, redistributable starter sound packs; no source WAVs were supplied."""

from __future__ import annotations

import hashlib
import importlib.util
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "globalPlugins" / "soundThemes"
ASSETS = ROOT / "globalPlugins" / "Sound Themes for NVDA" / "effects"
SPEC = importlib.util.spec_from_file_location("sound_catalog", SOURCE / "catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)

ROLES = """alert animation application article blockquote button calendar canvas caption cell chart checkbox checkmenuitem colorchooser column columnheader combobox comment complementary contentinfo datagrid dataitem definition deletion dialog directory document dropdownbutton editabletext embeddedobject endnote figure footer form frame graphic group grouping heading helpballoon hotspot icon image inputwindow label landmark link list listbox listitem log marquee math menu menubar menuitem menuitemcheckbox menuitemradio multilineedit outline outlineitem page pane paragraph passwordtext progressbar propertypage radiobutton radiomenuitem region rootpane row rowheader scrollarea scrollbar section separator slider spinbutton splitbutton statictext statusbar switch tab tabcontrol table tablecell tablecolumn tablerow terminal text titlebar togglebutton toolbar tooltip treeview treeviewitem video window""".split()
STATES = """active busy checked collapsed clickable default defunct draggable dragging drop_target editable enabled expanded focusable focused haspopup hidden invalid linked modal multiline offscreen pressed protected readonly required selected selectable sorted sorted_ascending sorted_descending visited""".split()


def tone(event: str, profile: int) -> bytes:
    """Soft 16-bit PCM sound that conveys event identity and direction."""
    digest = hashlib.sha256(event.encode("utf-8")).digest()
    base = (420, 590, 345)[profile] + digest[0] * 2.1
    if event.startswith("key."):
        length, base = 0.043, base * .84
    elif event.startswith("role."):
        length = 0.064
    elif event.startswith("state."):
        length = 0.074
    elif event.startswith("system."):
        length = 0.18
    else:
        length = 0.095
    direction = -1 if any(part in event for part in ("lock", "collapse", "close", "left", "down", "delete")) else 1
    if event in ("system.unlock", "nav.expand", "nav.open"):
        direction = 1
    rate = 22050
    samples = bytearray()
    for index in range(int(rate * length)):
        elapsed = index / rate
        x = elapsed / length
        envelope = min(1, elapsed / .006) * (1 - x) ** (2.25 if profile == 2 else 1.65)
        pitch = base * (1 + direction * x * .17)
        amplitude = (0.19, 0.13, 0.15)[profile]
        fundamental = math.sin(2 * math.pi * pitch * elapsed)
        overtone = math.sin(2 * math.pi * pitch * (1.51 if profile == 1 else 2.0) * elapsed)
        click = (math.sin(2 * math.pi * 4600 * elapsed) * math.exp(-elapsed * 125)
                 if event.startswith("key.") else 0)
        value = amplitude * envelope * (.82 * fundamental + .18 * overtone + .1 * click)
        samples.extend(struct.pack("<h", max(-32768, min(32767, round(value * 32767)))))
    return bytes(samples)


def generate():
    keys = {key for group in catalog.EVENT_GROUPS.values() for key in group}
    keys |= {f"role.{role.replace('_', '')}" for role in ROLES}
    keys |= {f"state.{state.replace('_', '')}" for state in STATES}
    keys |= {"role.default", "state.default"}
    for kind in ("navigation", "typing"):
        chosen = sorted(key for key in keys if catalog.is_typing_event(key) == (kind == "typing"))
        for index, (slug, display) in enumerate((("balanced", "Balanced"), ("bright", "Bright"), ("gentle", "Gentle"))):
            folder = ASSETS / kind / slug
            folder.mkdir(parents=True, exist_ok=True)
            for event in chosen:
                variants = 5 if event == "key.character" else 1
                for variant in range(variants):
                    filename = event + (f"__{variant}" if variant else "") + ".wav"
                    with wave.open(str(folder / filename), "wb") as output:
                        output.setnchannels(1)
                        output.setsampwidth(2)
                        output.setframerate(22050)
                        sound_key = event if variants == 1 else f"{event}.variant{variant + 1}"
                        output.writeframes(tone(sound_key, index))
            print(f"{kind}/{display}: {len(chosen)} event mappings, "
                  f"{sum(5 if event == 'key.character' else 1 for event in chosen)} WAV files")


if __name__ == "__main__":
    generate()
