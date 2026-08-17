#!/usr/bin/env python3

"""
Simple VL53L0X distance-sensor diagnostic.

This program verifies that Python can communicate with the VL53L0X
and continuously displays the measured distance in millimeters.

Press Ctrl+C to stop.
"""

import time

import board
import busio
import adafruit_vl53l0x


def main() -> None:
    print("=== VL53L0X Range Diagnostic ===")
    print("Initializing I2C and sensor...")

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
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
        while True:
            distance_mm = sensor.range
            print(f"{distance_mm:4d} mm")
            time.sleep(0.25)

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")


if __name__ == "__main__":
    main()
