#!/usr/bin/env python3

"""
Distance trigger/rearm diagnostic for Piano Staircase Demo 2.

Continuously reads the VL53L0X, passes measurements through DistanceTrigger, and displays the
current trigger state and state-change events.

Press Ctrl+C to stop.
"""

import argparse
import time

from piano_staircase_demo.sensor import DistanceSensor
from piano_staircase_demo.trigger import DistanceTrigger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test and calibrate Demo 2 distance trigger behavior."
    )

    parser.add_argument(
        "--trigger-mm",
        type=int,
        required=True,
        help="Distance at or below which a trigger may occur.",
    )

    parser.add_argument(
        "--rearm-mm",
        type=int,
        required=True,
        help="Distance at or above which the trigger may rearm.",
    )

    parser.add_argument(
        "--trigger-samples",
        type=int,
        default=2,
        help="Consecutive close readings required to trigger (default: 2).",
    )

    parser.add_argument(
        "--rearm-samples",
        type=int,
        default=3,
        help="Consecutive far readings required to rearm (default: 3).",
    )

    parser.add_argument(
        "--hz",
        type=float,
        default=10.0,
        help="Target sensor polling frequency in Hz (default: 10).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.hz <= 0:
        raise SystemExit("--hz must be greater than zero.")

    try:
        trigger = DistanceTrigger(
            trigger_distance_mm=args.trigger_mm,
            rearm_distance_mm=args.rearm_mm,
            trigger_samples=args.trigger_samples,
            rearm_samples=args.rearm_samples,
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid trigger configuration: {exc}") from exc

    print("=== Distance Trigger Diagnostic ===")
    print()
    print(f"Trigger distance:  {args.trigger_mm} mm")
    print(f"Rearm distance:    {args.rearm_mm} mm")
    print(f"Trigger samples:   {args.trigger_samples}")
    print(f"Rearm samples:     {args.rearm_samples}")
    print(f"Polling frequency: {args.hz:g} Hz")
    print()
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
    print("Press Ctrl+C to stop.")
    print()
    print("  time    distance   state       event")
    print("-----------------------------------------")

    interval = 1.0 / args.hz
    start_time = time.monotonic()
    next_sample = start_time

    try:
        with sensor:
            while True:
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(next_sample - now)

                sample_time = time.monotonic()
                distance_mm = sensor.distance_mm

                was_armed = trigger.armed
                fired = trigger.update(distance_mm)

                event = ""

                if fired:
                    event = "TRIGGER"
                elif not was_armed and trigger.armed:
                    event = "REARM"

                state = "ARMED" if trigger.armed else "DISARMED"
                elapsed = sample_time - start_time

                print(
                    f"{elapsed:6.2f}s   "
                    f"{distance_mm:4d} mm   "
                    f"{state:<10}  "
                    f"{event}"
                )

                next_sample += interval

                # If execution falls substantially behind, resume from now rather than trying to
                # rapidly catch up.
                if next_sample < time.monotonic() - interval:
                    next_sample = time.monotonic() + interval

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")


if __name__ == "__main__":
    main()
