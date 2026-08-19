"""
Reusable audio support for Piano Staircase Demo 2.

Audio may be generated programmatically or loaded from WAV assets and is
played through the current PipeWire default output. The module does not
depend on a particular physical audio device.
"""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
import tempfile
import wave
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


SAMPLE_RATE = 48_000
AMPLITUDE = 0.65
FADE_SECONDS = 0.01
PIPEWIRE_LATENCY = "25ms"

NOTES = {
    "C4": 261.63,
    "E4": 329.63,
    "G4": 392.00,
}


@dataclass(frozen=True)
class AudioClip:
    """An audio clip and its approximate duration."""

    path: Path
    duration_seconds: float


class AudioSystem:
    """Generate and play musical sequences through PipeWire."""

    def __init__(self) -> None:
        if shutil.which("pw-play") is None:
            raise RuntimeError(
                "pw-play was not found. "
                "Install PipeWire audio support before using AudioSystem."
            )

        self._temporary_directory = tempfile.TemporaryDirectory()
        self._directory = Path(self._temporary_directory.name)
        self._next_clip_number = 0
        self._process: subprocess.Popen | None = None
        self._closed = False

    @staticmethod
    def _append_silence(
        frames: bytearray,
        duration_seconds: float,
    ) -> None:
        """Append stereo silence to an audio buffer."""

        frame_count = int(SAMPLE_RATE * duration_seconds)
        frames.extend(b"\x00\x00\x00\x00" * frame_count)

    @staticmethod
    def _append_tone(
        frames: bytearray,
        frequency_hz: float,
        duration_seconds: float,
    ) -> None:
        """Append one stereo sine-wave tone to an audio buffer."""

        frame_count = int(SAMPLE_RATE * duration_seconds)
        fade_frames = int(SAMPLE_RATE * FADE_SECONDS)

        for frame in range(frame_count):
            time_seconds = frame / SAMPLE_RATE
            envelope = 1.0

            if fade_frames > 0:
                if frame < fade_frames:
                    envelope = frame / fade_frames
                elif frame >= frame_count - fade_frames:
                    envelope = (frame_count - frame - 1) / fade_frames

            sample = math.sin(
                2 * math.pi * frequency_hz * time_seconds
            )

            value = int(
                32767 * AMPLITUDE * envelope * sample
            )

            frames.extend(
                struct.pack("<hh", value, value)
            )

    def create_sequence(
        self,
        notes: Sequence[str],
        *,
        note_duration_seconds: float = 0.35,
        note_gap_seconds: float = 0.08,
        repetitions: int = 1,
        sequence_gap_seconds: float = 0.75,
        leading_silence_seconds: float = 0.0,
    ) -> AudioClip:
        """Generate a complete musical sequence as one WAV file."""

        if self._closed:
            raise RuntimeError("AudioSystem is closed.")

        if not notes:
            raise ValueError("At least one note is required.")

        if repetitions < 1:
            raise ValueError("repetitions must be at least 1.")

        for note in notes:
            if note not in NOTES:
                raise ValueError(f"Unknown note: {note}")

        frames = bytearray()

        self._append_silence(
            frames,
            leading_silence_seconds,
        )

        duration_seconds = leading_silence_seconds

        for repetition in range(repetitions):
            for index, note in enumerate(notes):
                self._append_tone(
                    frames,
                    NOTES[note],
                    note_duration_seconds,
                )

                duration_seconds += note_duration_seconds

                if index < len(notes) - 1:
                    self._append_silence(
                        frames,
                        note_gap_seconds,
                    )
                    duration_seconds += note_gap_seconds

            if repetition < repetitions - 1:
                self._append_silence(
                    frames,
                    sequence_gap_seconds,
                )
                duration_seconds += sequence_gap_seconds

        clip_path = (
            self._directory
            / f"sequence-{self._next_clip_number}.wav"
        )
        self._next_clip_number += 1

        with wave.open(str(clip_path), "w") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(frames)

        return AudioClip(
            path=clip_path,
            duration_seconds=duration_seconds,
        )

    @property
    def is_playing(self) -> bool:
        """Return whether a non-blocking playback is still active."""

        return (
            self._process is not None
            and self._process.poll() is None
        )

    def play(
        self,
        clip: AudioClip,
        *,
        blocking: bool = True,
    ) -> None:
        """Play an audio clip through the current PipeWire default sink."""

        if self._closed:
            raise RuntimeError("AudioSystem is closed.")

        if self.is_playing:
            raise RuntimeError("Audio playback is already active.")

        if blocking:
            subprocess.run(
                [
                    "pw-play",
                    f"--latency={PIPEWIRE_LATENCY}",
                    str(clip.path),
                ],
                check=True,
            )
            return

        self._process = subprocess.Popen(
            [
                "pw-play",
                f"--latency={PIPEWIRE_LATENCY}",
                str(clip.path),
            ],
        )

    def wait(self) -> None:
        """Wait for active non-blocking playback to finish."""

        if self._process is None:
            return

        self._process.wait()
        self._process = None

    def stop(self) -> None:
        """Stop active non-blocking playback."""

        if not self.is_playing:
            self._process = None
            return

        assert self._process is not None

        self._process.terminate()

        try:
            self._process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

        self._process = None

    def close(self) -> None:
        """Stop playback and release generated temporary files."""

        if self._closed:
            return

        self.stop()
        self._temporary_directory.cleanup()
        self._closed = True

    def __enter__(self) -> AudioSystem:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def load_wav(
        self,
        path: str | Path,
    ) -> AudioClip:
        """Load an existing uncompressed WAV file as an AudioClip."""

        if self._closed:
            raise RuntimeError("AudioSystem is closed.")

        clip_path = Path(path).expanduser().resolve()

        if not clip_path.is_file():
            raise FileNotFoundError(
                f"Audio file not found: {clip_path}"
            )

        try:
            with wave.open(str(clip_path), "rb") as wav:
                frame_count = wav.getnframes()
                frame_rate = wav.getframerate()
                compression = wav.getcomptype()

        except wave.Error as exc:
            raise ValueError(
                f"Unable to read WAV file: {clip_path}"
            ) from exc

        if compression != "NONE":
            raise ValueError(
                "Only uncompressed PCM WAV files are supported."
            )

        if frame_rate <= 0:
            raise ValueError(
                "WAV sample rate must be greater than zero."
            )

        return AudioClip(
            path=clip_path,
            duration_seconds=frame_count / frame_rate,
        )

    def create_metal_crash(
        self,
        *,
        duration_seconds: float = 1.0,
    ) -> AudioClip:
        """
        Generate a short metallic crash from inharmonic resonances.

        The effect combines several decaying non-harmonic frequencies with
        short noise bursts and secondary impacts to approximate struck and
        bouncing metal.
        """

        if self._closed:
            raise RuntimeError("AudioSystem is closed.")

        if duration_seconds <= 0:
            raise ValueError(
                "duration_seconds must be greater than zero."
            )

        frame_count = int(
            SAMPLE_RATE * duration_seconds
        )

        # Inharmonic resonances make the result sound more like metal than
        # a conventional musical chord.
        resonances = (
            (173.0, 0.42, 3.8),
            (257.0, 0.34, 4.3),
            (389.0, 0.28, 5.0),
            (557.0, 0.22, 5.8),
            (811.0, 0.16, 7.0),
            (1187.0, 0.11, 8.5),
        )

        # Main collision followed by two smaller bounces.
        impacts = (
            (0.000, 1.00),
            (0.075, 0.52),
            (0.185, 0.27),
        )

        # Fixed seed makes the generated effect reproducible.
        noise = random.Random(0x50495045)

        frames = bytearray()

        for frame in range(frame_count):
            time_seconds = frame / SAMPLE_RATE
            sample = 0.0

            for impact_time, impact_strength in impacts:
                local_time = (
                    time_seconds - impact_time
                )

                if local_time < 0:
                    continue

                ringing = 0.0

                for (
                    frequency,
                    strength,
                    decay,
                ) in resonances:
                    envelope = math.exp(
                        -decay * local_time
                    )

                    ringing += (
                        strength
                        * envelope
                        * math.sin(
                            2
                            * math.pi
                            * frequency
                            * local_time
                        )
                    )

                # A very short noise transient gives each collision a
                # sharper physical impact.
                impact_noise = (
                    noise.uniform(-1.0, 1.0)
                    * math.exp(-45.0 * local_time)
                )

                sample += impact_strength * (
                    ringing
                    + 0.65 * impact_noise
                )

            # Leave headroom because several resonances can overlap.
            sample *= 0.38

            sample = max(
                -1.0,
                min(1.0, sample),
            )

            value = int(
                32767 * sample
            )

            frames.extend(
                struct.pack("<hh", value, value)
            )

        clip_path = (
            self._directory
            / f"metal-crash-{self._next_clip_number}.wav"
        )

        self._next_clip_number += 1

        with wave.open(str(clip_path), "w") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(frames)

        return AudioClip(
            path=clip_path,
            duration_seconds=duration_seconds,
        )
