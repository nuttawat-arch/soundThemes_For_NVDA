"""Low-latency PCM-WAV playback using NVDA's own audio output (no BASS DLL)."""

from __future__ import annotations

import array
import queue
import random
import threading
import time
import wave
from pathlib import Path

from .catalog import candidates, is_keyboard_event, is_typing_event


def decode_pcm(path: Path, volume: int) -> tuple[tuple[int, int, int], bytes]:
    """Read and scale 8/16/24/32-bit PCM without deprecated audioop."""
    with wave.open(str(path), "rb") as audio:
        channels, width, rate = audio.getnchannels(), audio.getsampwidth(), audio.getframerate()
        if audio.getcomptype() != "NONE" or width not in (1, 2, 3, 4):
            raise ValueError("Unsupported PCM format")
        raw = audio.readframes(audio.getnframes())
    factor = max(0, min(100, int(volume))) / 100.0
    if factor == 1:
        return (channels, width * 8, rate), raw
    if width == 2:
        samples = array.array("h")
        samples.frombytes(raw)
        for index, sample in enumerate(samples):
            samples[index] = int(sample * factor)
        return (channels, 16, rate), samples.tobytes()
    if width == 1:
        return (channels, 8, rate), bytes(max(0, min(255, round(128 + (v - 128) * factor))) for v in raw)
    limit = (1 << (width * 8 - 1)) - 1
    data = bytearray()
    for index in range(0, len(raw), width):
        value = int.from_bytes(raw[index:index + width], "little", signed=True)
        value = max(-limit - 1, min(limit, int(value * factor)))
        data.extend(value.to_bytes(width, "little", signed=True))
    return (channels, width * 8, rate), bytes(data)


class _PlaybackVoice:
    """One reusable WASAPI stream. Only this voice's thread ever feeds it."""

    def __init__(self, number: int, closed: threading.Event, logger):
        self._closed = closed
        self._log = logger
        self._lock = threading.Lock()
        self._busy = False
        self._active_player = None
        self._jobs = queue.Queue(maxsize=1)
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"NVDA-SoundThemes-Voice-{number}",
        )
        self._thread.start()

    def offer(self, sound, device) -> bool:
        with self._lock:
            if self._busy or self._closed.is_set():
                return False
            self._busy = True
            self._jobs.put_nowait((sound, device))
            return True

    def _run(self):
        import nvwave

        player = None
        current_format = None
        try:
            while not self._closed.is_set():
                try:
                    (params, data), device = self._jobs.get(timeout=0.05)
                except queue.Empty:
                    continue
                try:
                    if (device, params) != current_format:
                        if player is not None:
                            player.close()
                        channels, bits, rate = params
                        kwargs = dict(
                            channels=channels, samplesPerSec=rate,
                            bitsPerSample=bits, outputDevice=device,
                            wantDucking=False,
                        )
                        if hasattr(nvwave, "AudioPurpose"):
                            kwargs["purpose"] = nvwave.AudioPurpose.SOUNDS
                        player = nvwave.WavePlayer(**kwargs)
                        current_format = (device, params)
                    with self._lock:
                        self._active_player = player
                    if self._closed.is_set():
                        continue
                    player.feed(data)
                    # feed() can block while WASAPI buffers; idle() waits only
                    # on THIS voice, so other sounds can play at once.
                    player.idle()
                except Exception as error:
                    self._log.warning("Sound Themes: audio voice failed: %s", error)
                    if player is not None:
                        try:
                            player.close()
                        except Exception:
                            pass
                    player = None
                    current_format = None
                finally:
                    with self._lock:
                        self._busy = False
                        self._active_player = None
        finally:
            if player is not None:
                try:
                    player.close()
                except Exception:
                    pass

    def close(self):
        # NVDA's WavePlayer.stop() also unblocks its native feed/sync when
        # shutting down. This only stops our own voice, on addon termination.
        with self._lock:
            player = self._active_player
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass
        self._thread.join(timeout=0.15)


class AudioEngine:
    # A bounded number of independent playback streams prevents a long WAV
    # from blocking short keystrokes without creating unbounded threads/buffers.
    MAX_VOICES = 12

    def __init__(self, output_device, logger):
        self._output_device = output_device
        self._log = logger
        self._sounds = {}
        self._typing_sounds = {}
        self._keyboard_sounds = {}
        self._last_played = {}
        # Retain a small burst, with newest-wins overflow; stale navigation
        # sounds must not accumulate while all playback voices are occupied.
        self._queue = queue.Queue(maxsize=self.MAX_VOICES)
        self._closed = threading.Event()
        self._preview_requests = queue.Queue(maxsize=1)
        self._preview_lock = threading.Lock()
        self._preview_serial = 0
        self._voices = [
            _PlaybackVoice(index, self._closed, self._log)
            for index in range(self.MAX_VOICES)
        ]
        self._worker = threading.Thread(target=self._run, daemon=True, name="NVDA-SoundThemes")
        self._worker.start()
        self._preview_worker = threading.Thread(
            target=self._run_previews, daemon=True, name="NVDA-SoundThemes-Preview",
        )
        self._preview_worker.start()

    def _load_bank(self, store, identifier: str, volume: int):
        """Atomically swap all cached audio. Never touch the playback thread's players."""
        loaded = {}
        try:
            folder = store.directory(identifier)
            sounds = store.load(identifier)["sounds"]
            decoded_by_filename = {}
            for event, value in sounds.items():
                options = []
                for relative in (value if isinstance(value, list) else [value]):
                    path = (folder / relative).resolve()
                    if not path.is_relative_to(folder.resolve()) or not path.is_file():
                        continue
                    try:
                        if path not in decoded_by_filename:
                            decoded_by_filename[path] = decode_pcm(path, volume)
                        options.append(decoded_by_filename[path])
                    except (OSError, ValueError, wave.Error) as error:
                        self._log.warning("Sound Themes: WAV %s skipped: %s", path.name, error)
                if options:
                    loaded[event] = options
        except (OSError, ValueError, KeyError) as error:
            self._log.warning("Sound Themes: theme unavailable: %s", error)
        return loaded

    def reload(self, navigation_store, navigation_id: str, typing_store, typing_id: str, volume: int,
               keyboard_store=None, keyboard_id: str = ""):
        self._sounds = self._load_bank(navigation_store, navigation_id, volume)
        self._typing_sounds = self._load_bank(typing_store, typing_id, volume)
        self._keyboard_sounds = (self._load_bank(keyboard_store, keyboard_id, volume)
                                 if keyboard_store is not None and keyboard_id else {})

    def _bank(self, event: str):
        if is_keyboard_event(event):
            return self._keyboard_sounds
        return self._typing_sounds if is_typing_event(event) else self._sounds

    def has_sound(self, event: str) -> bool:
        bank = self._bank(event)
        return any(key in bank for key in candidates(event))

    def has_exact_sound(self, event: str) -> bool:
        bank = self._bank(event)
        return event in bank

    def play(self, event: str, min_gap: float = 0.035):
        now = time.monotonic()
        if now - self._last_played.get(event, 0) < min_gap:
            return
        self._last_played[event] = now
        current = self._bank(event)
        options = next((current[c] for c in candidates(event) if c in current), None)
        if options is None or self._closed.is_set():
            return
        sound = options[0] if is_keyboard_event(event) else random.choice(options)
        self._enqueue_latest(sound)

    def _enqueue_latest(self, sound):
        """Never block NVDA: keep simultaneous cues unless the bounded queue fills."""
        try:
            self._queue.put_nowait(sound)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(sound)
            except queue.Full:
                pass  # A newer event won the race; never reorder it.

    def preview_file(self, path: Path, volume: int):
        """Schedule a latest-only audition; decoding never blocks wx/NVDA UI."""
        if self._closed.is_set():
            return
        with self._preview_lock:
            self._preview_serial += 1
            request = (self._preview_serial, Path(path), volume)
        try:
            self._preview_requests.put_nowait(request)
        except queue.Full:
            try:
                self._preview_requests.get_nowait()
            except queue.Empty:
                pass
            try:
                self._preview_requests.put_nowait(request)
            except queue.Full:
                pass

    def _run_previews(self):
        # Cache a handful of recently visited files. This is separate from the
        # active theme bank so changing the preview never switches a theme.
        cache = {}
        while not self._closed.is_set():
            try:
                serial, path, volume = self._preview_requests.get(timeout=0.05)
            except queue.Empty:
                continue
            while True:
                try:
                    serial, path, volume = self._preview_requests.get_nowait()
                except queue.Empty:
                    break
            try:
                cache_key = (path, volume, path.stat().st_mtime_ns)
                sound = cache.get(cache_key)
                if sound is None:
                    sound = decode_pcm(path, volume)
                    if len(cache) >= 8:
                        cache.pop(next(iter(cache)))
                    cache[cache_key] = sound
                with self._preview_lock:
                    newest = serial == self._preview_serial
                if newest and not self._closed.is_set():
                    self._enqueue_latest(sound)
            except (OSError, ValueError, wave.Error) as error:
                self._log.warning("Sound Themes: preview WAV skipped: %s", error)

    def _run(self):
        pending = None
        while not self._closed.is_set():
            if pending is None:
                try:
                    pending = self._queue.get(timeout=0.05)
                except queue.Empty:
                    continue
            for voice in self._voices:
                if self._closed.is_set():
                    break
                try:
                    device = self._output_device()
                    if voice.offer(pending, device):
                        pending = None
                        break
                except Exception as error:
                    self._log.warning("Sound Themes: audio dispatch failed: %s", error)
                    pending = None
                    break
            else:
                # All streams are busy. Drop superseded waiting focus cues,
                # but do not touch any audio already playing on other streams.
                try:
                    pending = self._queue.get(timeout=0.015)
                    while True:
                        pending = self._queue.get_nowait()
                except queue.Empty:
                    pass

    def close(self):
        self._closed.set()
        self._preview_worker.join(timeout=0.4)
        self._worker.join(timeout=0.4)
        for voice in self._voices:
            voice.close()
