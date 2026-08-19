#!/usr/bin/env python3

"""
Piano Staircase Demo 2 application.

Runs the current interactive tabletop demonstration using:

    VL53L0X distance sensing
        -> proximity trigger/rearm logic
        -> interaction rate limiting
        -> synchronized musical note and lighting response

Accepted interactions cycle through:

    C4 -> GREEN
    E4 -> YELLOW
    G4 -> BLUE

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
from piano_staircase_demo.modes import (
    CycleMode,
    DistanceMode,
    InteractionResponse,
    RandomMode,
)


# Current validated Demo 2 defaults.
TRIGGER_DISTANCE_MM = 500
REARM_DISTANCE_MM = 750

TRIGGER_SAMPLES = 1
REARM_SAMPLES = 1

POLL_HZ = 30.0
COOLDOWN_SECONDS = 0.20

NOTE_DURATION_SECONDS = 0.15
LIGHT_BRIGHTNESS_PERCENT = 100

RESPONSE_MODE = "cycle"

RESPONSES = (
    InteractionResponse(
        note="C4",
        light_name="green",
    ),
    InteractionResponse(
        note="E4",
        light_name="yellow",
    ),
    InteractionResponse(
        note="G4",
        light_name="blue",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Piano Staircase Demo 2 tabletop application."
    )

    parser.add_argument(
        "--trigger-mm",
        type=int,
        default=TRIGGER_DISTANCE_MM,
        help=(
            "Trigger distance in millimeters "
            f"(default: {TRIGGER_DISTANCE_MM})."
        ),
    )

    parser.add_argument(
        "--rearm-mm",
        type=int,
        default=REARM_DISTANCE_MM,
        help=(
            "Rearm distance in millimeters "
            f"(default: {REARM_DISTANCE_MM})."
        ),
    )

    parser.add_argument(
        "--trigger-samples",
        type=int,
        default=TRIGGER_SAMPLES,
        help=(
            "Consecutive trigger samples "
            f"(default: {TRIGGER_SAMPLES})."
        ),
    )

    parser.add_argument(
        "--rearm-samples",
        type=int,
        default=REARM_SAMPLES,
        help=(
            "Consecutive rearm samples "
            f"(default: {REARM_SAMPLES})."
        ),
    )

    parser.add_argument(
        "--hz",
        type=float,
        default=POLL_HZ,
        help=f"Sensor polling frequency (default: {POLL_HZ:g} Hz).",
    )

    parser.add_argument(
        "--cooldown",
        type=float,
        default=COOLDOWN_SECONDS,
        help=(
            "Minimum interval between accepted interactions "
            f"(default: {COOLDOWN_SECONDS:.2f} seconds)."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display dropped and invalid interactions.",
    )

    parser.add_argument(
        "--response-mode",
        choices=("cycle", "random", "distance"),
        default=RESPONSE_MODE,
        help=(
            "How accepted interactions select responses "
            f"(default: {RESPONSE_MODE})."
        ),
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
    signal.signal(signal.SIGTERM, request_stop)

    try:
        trigger = DistanceTrigger(
            trigger_distance_mm=args.trigger_mm,
            rearm_distance_mm=args.rearm_mm,
            trigger_samples=args.trigger_samples,
            rearm_samples=args.rearm_samples,
        )

        gate = CooldownGate(args.cooldown)
        if args.response_mode == "cycle":
            mode = CycleMode(RESPONSES)

        elif args.response_mode == "random":
            mode = RandomMode(RESPONSES)

        elif args.response_mode == "distance":
            mode = DistanceMode(
                RESPONSES,
                minimum_distance_mm=1,
                maximum_distance_mm=args.trigger_mm,
            )

        else:
            raise AssertionError(
                f"Unhandled response mode: {args.response_mode}"
            )

    except ValueError as exc:
        raise SystemExit(f"Invalid configuration: {exc}") from exc

    print("=== Piano Staircase Demo 2 ===")
    print()
    print("C4 -> GREEN")
    print("E4 -> YELLOW")
    print("G4 -> BLUE")
    print()
    print(f"Response mode: {args.response_mode}")
    print()
    print("Initializing hardware...")

    interval = 1.0 / args.hz

    try:
        with (
            DistanceSensor() as sensor,
            LightingSystem() as lights,
            AudioSystem() as audio,
        ):
            channels = {
                "green": lights.green,
                "yellow": lights.yellow,
                "blue": lights.blue,
            }

            # Generate the short note clips once during startup rather than
            # rebuilding audio on every interaction.
            clips = {
                response.note: audio.create_sequence(
                    (response.note,),
                    note_duration_seconds=NOTE_DURATION_SECONDS,
                )
                for response in RESPONSES
            }

            lights.all_off()

            print("Ready.")
            print("Press Ctrl+C to stop.")
            print()

            next_sample = time.monotonic()

            active_channel = None
            light_off_time = 0.0

            while not stop_requested:
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(next_sample - now)

                sample_time = time.monotonic()

                # Lighting is timed without blocking the sensor loop.
                if (
                    active_channel is not None
                    and sample_time >= light_off_time
                ):
                    active_channel.off()
                    active_channel = None

                distance_mm = sensor.distance_mm

                if distance_mm is None:
                    if args.verbose:
                        print("INVALID SENSOR SAMPLE")

                    next_sample += interval
                    continue

                fired = trigger.update(distance_mm)

                if fired:
                    # Never overlap pw-play processes.
                    if audio.is_playing:
                        if args.verbose:
                            print(
                                f"{distance_mm:4d} mm -> "
                                "DROP AUDIO BUSY"
                            )

                    # Only consume the cooldown when audio is actually
                    # available to accept the interaction.
                    elif not gate.allow():
                        if args.verbose:
                            print(
                                f"{distance_mm:4d} mm -> "
                                "DROP COOLDOWN"
                            )

                    else:
                        response = mode.next_response(distance_mm)

                        note = response.note
                        clip = clips[note]
                        channel = channels[response.light_name]

                        if active_channel is not None:
                            active_channel.off()

                        channel.set_brightness(
                            LIGHT_BRIGHTNESS_PERCENT
                        )

                        active_channel = channel

                        # Use a fresh timestamp here so the light duration
                        # begins when the response actually starts rather
                        # than before the sensor read.
                        response_time = time.monotonic()

                        light_off_time = (
                            response_time
                            + NOTE_DURATION_SECONDS
                        )

                        audio.play(
                            clip,
                            blocking=False,
                        )

                        print(
                            f"{note} -> {channel.name}"
                        )

                next_sample += interval

                # If a hardware or OS operation temporarily delays the loop,
                # resume from the current time instead of rapidly trying to
                # replay missed polling intervals.
                if next_sample < time.monotonic() - interval:
                    next_sample = (
                        time.monotonic()
                        + interval
                    )

    except KeyboardInterrupt:
        pass

    finally:
        print()
        print("Demo stopped.")


if __name__ == "__main__":
    main()
