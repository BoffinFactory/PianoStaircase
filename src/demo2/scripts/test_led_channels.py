#!/usr/bin/env python3

"""
Three-channel lighting diagnostic for Piano Staircase Demo 2.

Tests the reusable lighting module against the green, yellow, and blue
transistor-controlled channels.

Press Ctrl+C to stop early.
"""

import time

from piano_staircase_demo.lighting import LightingSystem


def main() -> None:
    print("=== Piano Staircase Three-Channel Lighting Diagnostic ===")
    print()

    try:
        with LightingSystem() as lights:
            print("Testing individual brightness levels...")

            for channel in lights.channels:
                print(f"Testing {channel.name}...")

                for brightness in (25, 50, 75, 100):
                    print(f"  {brightness:3d}%")
                    channel.set_brightness(brightness)
                    time.sleep(0.75)

                channel.off()
                time.sleep(0.5)

            print()
            print("Testing staircase sequence...")

            for _ in range(3):
                for channel in lights.channels:
                    print(f"  {channel.name}")
                    channel.set_brightness(100)
                    time.sleep(0.4)
                    channel.off()

            print()
            print("Testing individual fades...")

            for channel in lights.channels:
                print(f"  Fading {channel.name}")
                channel.fade_to(100)
                channel.fade_to(0)

            print()
            print("Testing simultaneous fade...")

            for _ in range(3):
                lights.fade_all_to(100)
                lights.fade_all_to(0)

            print()
            print("Diagnostic complete.")

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")

    finally:
        print("All channels OFF.")


if __name__ == "__main__":
    main()
