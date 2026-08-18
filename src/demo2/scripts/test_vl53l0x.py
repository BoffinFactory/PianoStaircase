#!/usr/bin/env python3

"""
VL53L0X distance-sensor diagnostic for Piano Staircase Demo 2.

Continuously displays the measured distance in millimeters.

Press Ctrl+C to stop.
"""

import time

from piano_staircase_demo.sensor import DistanceSensor


def main() -> None:
    print("=== VL53L0X Range Diagnostic ===")
    print("Initializing sensor...")

    try:
        sensor = DistanceSensor()
    except Exception as exc:
        print()
        print("ERROR: Unable to initialize the VL53L0X.")
        print()
        print("Check that:")
        print("  - I2C is enabled")
        print("  - the sensor is powered")
        print("  - SDA and SCL are connected correctly")
        print("  - 'i2cdetect -y 1' shows address 0x29")
        print()
        print(f"Python error: {exc}")
        raise SystemExit(1) from exc

    print("Sensor initialized successfully.")
    print("Move an object toward or away from the sensor.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        with sensor:
            while True:
                print(f"{sensor.distance_mm:4d} mm")
                time.sleep(0.25)

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")


if __name__ == "__main__":
    main()
