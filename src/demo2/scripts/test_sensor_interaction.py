#!/usr/bin/env python3

"""
Sensor-to-interaction diagnostic for Piano Staircase Demo 2.

Combines the VL53L0X distance sensor, proximity trigger logic, and interaction cooldown gate without
starting audio or lighting.

Press Ctrl+C to stop.
"""

import argparse
import signal
import time

from piano_staircase_demo.interaction import CooldownGate
from piano_staircase_demo.sensor import DistanceSensor
from piano_staircase_demo.trigger import DistanceTrigger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test the complete Demo 2 sensor interaction path."
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
        default=1,
        help="Consecutive close readings required to trigger (default: 1).",
    )

    parser.add_argument(
        "--rearm-samples",
        type=int,
        default=1,
        help="Consecutive far readings required to rearm (default: 1).",
    )

    parser.add_argument(
        "--hz",
        type=float,
        default=30.0,
        help="Target sensor polling frequency in Hz (default: 30).",
    )

    parser.add_argument(
        "--cooldown",
        type=float,
        default=0.20,
        help="Minimum seconds between accepted interactions (default: 0.20).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.hz <= 0:
        raise SystemExit("--hz must be greater than zero.")

    stop_requested = False

    def request_stop(signum, frame) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)

    try:
        trigger = DistanceTrigger(
            trigger_distance_mm=args.trigger_mm,
            rearm_distance_mm=args.rearm_mm,
            trigger_samples=args.trigger_samples,
            rearm_samples=args.rearm_samples,
        )

        gate = CooldownGate(args.cooldown)

    except ValueError as exc:
        raise SystemExit(f"Invalid configuration: {exc}") from exc

    print("=== Sensor Interaction Diagnostic ===")
    print()
    print(f"Trigger distance:  {args.trigger_mm} mm")
    print(f"Rearm distance:    {args.rearm_mm} mm")
    print(f"Trigger samples:   {args.trigger_samples}")
    print(f"Rearm samples:     {args.rearm_samples}")
    print(f"Polling frequency: {args.hz:g} Hz")
    print(f"Cooldown:          {args.cooldown:.3f} s")
    print()
    print("Initializing sensor...")

    try:
        sensor = DistanceSensor()
    except Exception as exc:
        print()
        print("ERROR: Unable to initialize the VL53L0X.")
        print(f"Python error: {exc}")
        raise SystemExit(1) from exc

    print("Sensor initialized successfully.")
    print("Wave an object through the trigger area rapidly.")
    print("Press Ctrl+C to stop.")
    print()
    print("  time    distance   sensor event   application")
    print("------------------------------------------------")

    interval = 1.0 / args.hz
    start_time = time.monotonic()
    next_sample = start_time

    trigger_count = 0
    accepted_count = 0
    dropped_count = 0
    invalid_count = 0

    try:
        with sensor:
            while not stop_requested:
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(next_sample - now)

                sample_time = time.monotonic()
                elapsed = sample_time - start_time

                distance_mm = sensor.distance_mm

                if distance_mm is None:
                    invalid_count += 1
                    print(
                        f"{elapsed:6.2f}s   "
                        f"{'----':>7}   "
                        f"{'INVALID':<12}"
                    )

                    next_sample += interval
                    continue

                was_armed = trigger.armed
                fired = trigger.update(distance_mm)

                if fired:
                    trigger_count += 1

                    if gate.allow():
                        accepted_count += 1
                        application = "ACCEPT"
                    else:
                        dropped_count += 1
                        application = "DROP"

                    print(
                        f"{elapsed:6.2f}s   "
                        f"{distance_mm:4d} mm   "
                        f"{'TRIGGER':<12}   "
                        f"{application}"
                    )

                elif not was_armed and trigger.armed:
                    print(
                        f"{elapsed:6.2f}s   "
                        f"{distance_mm:4d} mm   "
                        f"{'REARM':<12}"
                    )

                next_sample += interval

                if next_sample < time.monotonic() - interval:
                    next_sample = time.monotonic() + interval

    except KeyboardInterrupt:
        pass
    finally:
        print()
        print("Diagnostic stopped.")
        print()
        print("Summary:")
        print(f"  Triggers detected:      {trigger_count}")
        print(f"  Interactions accepted:  {accepted_count}")
        print(f"  Interactions dropped:   {dropped_count}")
        print(f"  Invalid sensor samples: {invalid_count}")


if __name__ == "__main__":
    main()
