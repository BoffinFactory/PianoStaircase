#!/usr/bin/env python3

"""
Full interaction diagnostic for Piano Staircase Demo 2.

Combines distance sensing, trigger/rearm behavior, interaction rate limiting, short musical notes,
and matching lighting feedback.

Accepted interactions cycle through:

    C4 -> GREEN E4 -> YELLOW G4 -> BLUE

Press Ctrl+C to stop.
"""

import argparse
import signal
import time

from piano_staircase_demo.audio import AudioSystem
from piano_staircase_demo.interaction import CooldownGate
from piano_staircase_demo.lighting import LightingSystem
from piano_staircase_demo.sensor import DistanceSensor
from piano_staircase_demo.trigger import DistanceTrigger


NOTES = ("C4", "E4", "G4")

NOTE_DURATION_SECONDS = 0.15
LIGHT_BRIGHTNESS_PERCENT = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test the complete Demo 2 interaction path."
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

    print("=== Full Piano Staircase Interaction Diagnostic ===")
    print()
    print("C4 -> GREEN")
    print("E4 -> YELLOW")
    print("G4 -> BLUE")
    print()
    print(f"Trigger distance:  {args.trigger_mm} mm")
    print(f"Rearm distance:    {args.rearm_mm} mm")
    print(f"Trigger samples:   {args.trigger_samples}")
    print(f"Rearm samples:     {args.rearm_samples}")
    print(f"Polling frequency: {args.hz:g} Hz")
    print(f"Cooldown:          {args.cooldown:.3f} s")
    print(f"Note duration:     {NOTE_DURATION_SECONDS:.3f} s")
    print()
    print("Initializing hardware...")

    interval = 1.0 / args.hz

    trigger_count = 0
    played_count = 0
    cooldown_drop_count = 0
    busy_drop_count = 0
    invalid_count = 0

    try:
        with (
            DistanceSensor() as sensor,
            LightingSystem() as lights,
            AudioSystem() as audio,
        ):
            channels = (
                lights.green,
                lights.yellow,
                lights.blue,
            )

            clips = tuple(
                audio.create_sequence(
                    (note,),
                    note_duration_seconds=NOTE_DURATION_SECONDS,
                )
                for note in NOTES
            )

            lights.all_off()

            print("Hardware initialized successfully.")
            print("Wave an object through the trigger area.")
            print("Press Ctrl+C to stop.")
            print()
            print("  time    distance   event       result")
            print("--------------------------------------------")

            start_time = time.monotonic()
            next_sample = start_time

            next_note_index = 0

            active_channel = None
            light_off_time = 0.0

            while not stop_requested:
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(next_sample - now)

                sample_time = time.monotonic()
                elapsed = sample_time - start_time

                # Turn off the active light when its short flash expires. This is deliberately
                # handled from the main loop so sensing does not pause while the light is on.
                if (
                    active_channel is not None
                    and sample_time >= light_off_time
                ):
                    active_channel.off()
                    active_channel = None

                distance_mm = sensor.distance_mm

                if distance_mm is None:
                    invalid_count += 1

                    print(
                        f"{elapsed:6.2f}s   "
                        f"{'----':>7}   "
                        f"{'INVALID':<10}"
                    )

                    next_sample += interval
                    continue

                fired = trigger.update(distance_mm)

                if fired:
                    trigger_count += 1

                    if audio.is_playing:
                        busy_drop_count += 1

                        print(
                            f"{elapsed:6.2f}s   "
                            f"{distance_mm:4d} mm   "
                            f"{'TRIGGER':<10}  "
                            f"DROP AUDIO BUSY"
                        )

                    elif not gate.allow():
                        cooldown_drop_count += 1

                        print(
                            f"{elapsed:6.2f}s   "
                            f"{distance_mm:4d} mm   "
                            f"{'TRIGGER':<10}  "
                            f"DROP COOLDOWN"
                        )

                    else:
                        note = NOTES[next_note_index]
                        clip = clips[next_note_index]
                        channel = channels[next_note_index]

                        # The previous flash should normally have expired before another accepted
                        # interaction, but explicitly turn it off if necessary.
                        if active_channel is not None:
                            active_channel.off()

                        channel.set_brightness(
                            LIGHT_BRIGHTNESS_PERCENT
                        )

                        active_channel = channel
                        light_off_time = (
                            sample_time
                            + NOTE_DURATION_SECONDS
                        )

                        audio.play(
                            clip,
                            blocking=False,
                        )

                        played_count += 1

                        print(
                            f"{elapsed:6.2f}s   "
                            f"{distance_mm:4d} mm   "
                            f"{'TRIGGER':<10}  "
                            f"PLAY {note}"
                        )

                        next_note_index = (
                            next_note_index + 1
                        ) % len(NOTES)

                next_sample += interval

                # Avoid rapidly trying to catch up if something temporarily makes the loop fall
                # substantially behind schedule.
                if next_sample < time.monotonic() - interval:
                    next_sample = (
                        time.monotonic()
                        + interval
                    )

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print()
        print(f"ERROR: {exc}")
        raise
    finally:
        print()
        print("Diagnostic stopped.")
        print()
        print("Summary:")
        print(f"  Triggers detected:      {trigger_count}")
        print(f"  Notes played:           {played_count}")
        print(f"  Cooldown drops:         {cooldown_drop_count}")
        print(f"  Audio-busy drops:       {busy_drop_count}")
        print(f"  Invalid sensor samples: {invalid_count}")


if __name__ == "__main__":
    main()
