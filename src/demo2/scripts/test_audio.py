#!/usr/bin/env python3

"""
Audio diagnostic for Piano Staircase Demo 2.

Generates and plays a C4-E4-G4 musical sequence through the current PipeWire default output.

Press Ctrl+C to stop early.
"""

import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path


SAMPLE_RATE = 48_000
AMPLITUDE = 0.65

NOTE_DURATION_SECONDS = 0.35
NOTE_GAP_SECONDS = 0.08
SEQUENCE_GAP_SECONDS = 0.75
FADE_SECONDS = 0.01

NOTES = {
    "C4": 261.63,
    "E4": 329.63,
    "G4": 392.00,
}

SEQUENCE = ("C4", "E4", "G4")


def write_silence(wav: wave.Wave_write, duration_seconds: float) -> None:
    """Write stereo silence to an open WAV file."""

    frame_count = int(SAMPLE_RATE * duration_seconds)
    silent_frame = struct.pack("<hh", 0, 0)

    for _ in range(frame_count):
        wav.writeframesraw(silent_frame)


def write_tone(
    wav: wave.Wave_write,
    frequency_hz: float,
    duration_seconds: float,
) -> None:
    """Write one stereo sine-wave tone to an open WAV file."""

    frame_count = int(SAMPLE_RATE * duration_seconds)
    fade_frames = int(SAMPLE_RATE * FADE_SECONDS)

    for frame in range(frame_count):
        time_seconds = frame / SAMPLE_RATE

        envelope = 1.0

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

        wav.writeframesraw(
            struct.pack("<hh", value, value)
        )


def create_sequence(path: Path) -> None:
    """Generate the complete diagnostic as one continuous WAV file."""

    with wave.open(str(path), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)

        # Give the audio stream a short period to become established before the first audible note.
        write_silence(wav, 0.5)

        for repetition in range(3):
            for index, note in enumerate(SEQUENCE):
                write_tone(
                    wav,
                    NOTES[note],
                    NOTE_DURATION_SECONDS,
                )

                if index < len(SEQUENCE) - 1:
                    write_silence(
                        wav,
                        NOTE_GAP_SECONDS,
                    )

            if repetition < 2:
                write_silence(
                    wav,
                    SEQUENCE_GAP_SECONDS,
                )


def main() -> None:
    print("=== Piano Staircase Audio Diagnostic ===")
    print()
    print("Generating C4-E4-G4 test sequence...")

    with tempfile.TemporaryDirectory() as temp_directory:
        sequence_path = (
            Path(temp_directory)
            / "piano-staircase-audio-test.wav"
        )

        create_sequence(sequence_path)

        print("Playing sequence...")
        print()

        subprocess.run(
            ["pw-play", str(sequence_path)],
            check=True,
        )

    print()
    print("Diagnostic complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")
