#!/usr/bin/env python3

"""Turn the green lighting channel on at full brightness for 10 seconds."""

import time

from piano_staircase_demo.lighting import LightingSystem


def main() -> None:
    print("Turning GREEN LEDs on for 10 seconds...")

    try:
        with LightingSystem() as lights:
            lights.green.set_brightness(100)
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nStopped early.")

    finally:
        print("GREEN LEDs off.")


if __name__ == "__main__":
    main()
