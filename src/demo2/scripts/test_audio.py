#!/usr/bin/env python3

"""
Audio diagnostic for Piano Staircase Demo 2.

Generates and plays the C4, E4, and G4 notes used by the tabletop demo. Audio is sent to the current
PipeWire default output.

Press Ctrl+C to stop early.
"""

import math
import struct
import subprocess
import tempfile
import time
import wave
from pathlib import Path


SAMPLE_RATE = 48_000
NOTE_DURATION_SECONDS = 0.35
AMPLITUDE = 0.65
FADE_SECONDS = 0.01

NOTES = {
    "C4": 261.63,
    "E4": 329.63,
    "G4": 392.00,
}


def create_tone(path: Path, frequency_hz: float) -> None:
    """Generate a stereo WAV file containing one sine-wave tone."""

    frame_count = int(SAMPLE_RATE * NOTE_DURATION_SECONDS)
    fade_frames = int(SAMPLE_RATE * FADE_SECONDS)

    with wave.open(str(path), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)

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


def play_tone(path: Path) -> None:
    """Play a WAV file through the current PipeWire default output."""

    subprocess.run(
        ["pw-play", str(path)],
        check=True,
    )


def main() -> None:
    print("=== Piano Staircase Audio Diagnostic ===")
    print()

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)

        tone_paths = {}

        for note, frequency in NOTES.items():
            path = temp_path / f"{note.lower()}.wav"
            create_tone(path, frequency)
            tone_paths[note] = path

        print("Testing individual notes...")

        for note, path in tone_paths.items():
            print(f"  {note}")
            play_tone(path)
            time.sleep(0.5)

        print()
        print("Testing C-E-G sequence...")

        for _ in range(3):
            for note in ("C4", "E4", "G4"):
                print(f"  {note}")
                play_tone(tone_paths[note])

            time.sleep(0.75)

        print()
        print("Diagnostic complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")
