#!/usr/bin/env python3

"""
Audio diagnostic for Piano Staircase Demo 2.

Generates and plays a C4-E4-G4 musical sequence through the current PipeWire default output.

Press Ctrl+C to stop early.
"""

from piano_staircase_demo.audio import AudioSystem


def main() -> None:
    print("=== Piano Staircase Audio Diagnostic ===")
    print()
    print("Generating C4-E4-G4 test sequence...")

    with AudioSystem() as audio:
        sequence = audio.create_sequence(
            ("C4", "E4", "G4"),
            repetitions=3,
            leading_silence_seconds=0.5,
        )

        print(
            f"Sequence duration: "
            f"{sequence.duration_seconds:.2f} seconds"
        )
        print()
        print("Playing sequence...")
        print()

        audio.play(sequence)

    print()
    print("Diagnostic complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")
