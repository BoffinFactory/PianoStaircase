#!/usr/bin/env python3

"""
Compare synthesized and recorded pipe-crash audio.

The synthesized effect is always played. An optional WAV file may also
be supplied for comparison.
"""

import argparse

from piano_staircase_demo.audio import AudioSystem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Demo 2 pipe-crash audio."
    )

    parser.add_argument(
        "--wav",
        help="Optional recorded WAV file to play after the synthesized effect.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with AudioSystem() as audio:
        print("Generating synthesized metal crash...")

        synthesized = audio.create_metal_crash()

        print("Playing synthesized crash...")
        audio.play(synthesized)

        if args.wav is not None:
            print()
            print(f"Loading recorded sound: {args.wav}")

            recorded = audio.load_wav(args.wav)

            print(
                "Recorded duration: "
                f"{recorded.duration_seconds:.3f} seconds"
            )

            print("Playing recorded sound...")
            audio.play(recorded)

    print()
    print("Comparison complete.")


if __name__ == "__main__":
    main()
