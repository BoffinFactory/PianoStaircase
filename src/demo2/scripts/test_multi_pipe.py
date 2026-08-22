#!/usr/bin/env python3

"""
Interactive multi-pipe scheduler test for Piano Staircase Demo 2.

Commands are line-oriented. Type a command and press Enter while existing
pipes are still falling.

    p          launch one random pipe
    p <seed>   launch a reproducible pipe
    b          fill every available pipe slot at once
    s          show currently active pipe physics
    q          quit

Press Ctrl+C to stop.
"""

from __future__ import annotations

import select
import signal
import sys
import time

from piano_staircase_demo.pipes import (
    PipeSnapshot,
    PipeSystem,
)
from piano_staircase_demo.synth import (
    FluidSynthEngine,
)


UPDATE_HZ = 200.0


def print_pipe(
    pipe: PipeSnapshot,
) -> None:
    """Print the physical properties of one newly launched pipe."""

    print()
    print(
        f"PIPE #{pipe.pipe_id} "
        f"[MIDI channel {pipe.channel}]"
    )

    print(
        f"  seed:           "
        f"{pipe.seed}"
    )

    print(
        f"  material:       "
        f"{pipe.material}"
    )

    print(
        f"  length:         "
        f"{pipe.length_m:.2f} m"
    )

    print(
        f"  diameter:       "
        f"{pipe.outer_diameter_mm:.1f} mm"
    )

    print(
        f"  wall thickness: "
        f"{pipe.wall_thickness_mm:.1f} mm"
    )

    print(
        f"  restitution:    "
        f"{pipe.restitution:.2f}"
    )

    print(
        f"  resonances:     "
        f"{pipe.low_resonance} / "
        f"{pipe.high_resonance}"
    )

    print(
        f"  impacts:        "
        f"{pipe.impact_count}"
    )

    print()


def launch_pipe(
    pipes: PipeSystem,
    *,
    seed: int | None = None,
) -> None:
    """Launch and describe one pipe."""

    pipe = pipes.start_pipe(
        seed=seed
    )

    if pipe is None:
        print(
            "No pipe channels available."
        )

        return

    print_pipe(
        pipe
    )


def print_status(
    pipes: PipeSystem,
) -> None:
    """Print state for every currently active pipe."""

    snapshots = (
        pipes.snapshots()
    )

    print()
    print(
        f"Active pipes: "
        f"{pipes.active_count} / "
        f"{pipes.maximum_pipes}"
    )

    if not snapshots:
        print(
            "  none"
        )

        print()

        return

    for pipe in snapshots:
        if (
            pipe.next_impact_seconds
            is None
        ):
            next_text = (
                "final contact"
            )

        else:
            next_text = (
                f"{pipe.next_impact_seconds:.3f} s"
            )

        print(
            f"  #{pipe.pipe_id:<3} "
            f"{pipe.material:<8} "
            f"{pipe.length_m:.2f} m  "
            f"impact "
            f"{pipe.impact_number}/"
            f"{pipe.impact_count}  "
            f"next {next_text}"
        )

    print()


def process_command(
    command: str,
    pipes: PipeSystem,
) -> bool:
    """
    Process one interactive command.

    Return False when the program should exit.
    """

    command = (
        command
        .strip()
        .lower()
    )

    if not command:
        return True

    if command == "q":
        return False

    if command == "p":
        launch_pipe(
            pipes
        )

        return True

    if command.startswith(
        "p "
    ):
        try:
            seed = int(
                command.split(
                    maxsplit=1
                )[1]
            )

        except ValueError:
            print(
                "Seed must be an integer."
            )

            return True

        launch_pipe(
            pipes,
            seed=seed,
        )

        return True

    if command == "b":
        count = (
            pipes.available_slots
        )

        if count == 0:
            print(
                "All pipe channels are already occupied."
            )

            return True

        print()
        print(
            f"Launching {count} pipes simultaneously..."
        )

        for _ in range(
            count
        ):
            launch_pipe(
                pipes
            )

        return True

    if command == "s":
        print_status(
            pipes
        )

        return True

    print(
        "Commands: p, p <seed>, b, s, q"
    )

    return True


def main(
) -> None:
    """Run the interactive nonblocking multi-pipe test."""

    stop_requested = False

    def request_stop(
        signum,
        frame,
    ) -> None:
        nonlocal stop_requested

        stop_requested = True

    signal.signal(
        signal.SIGINT,
        request_stop,
    )

    signal.signal(
        signal.SIGTERM,
        request_stop,
    )

    interval = (
        1.0
        / UPDATE_HZ
    )

    print(
        "=== Multi-Pipe Physics Test ==="
    )

    print()
    print(
        "Commands:"
    )

    print(
        "  p          launch one random pipe"
    )

    print(
        "  p <seed>   replay a specific pipe"
    )

    print(
        "  b          launch all available pipes"
    )

    print(
        "  s          show active pipe physics"
    )

    print(
        "  q          quit"
    )

    print()
    print(
        "Commands remain available while pipes are falling."
    )

    print()

    with FluidSynthEngine() as synth:
        pipes = PipeSystem(
            synth
        )

        try:
            while not stop_requested:
                loop_start = (
                    time.monotonic()
                )

                #
                # Advance every physical simulation.
                #
                events = (
                    pipes.update(
                        now=loop_start
                    )
                )

                for event in events:
                    if (
                        event.kind
                        == "impact"
                    ):
                        print(
                            f"#{event.pipe_id} "
                            f"impact "
                            f"{event.impact_number}/"
                            f"{event.impact_count} "
                            f"[{event.primary_note}/"
                            f"{event.secondary_note}]"
                        )

                    elif (
                        event.kind
                        == "complete"
                    ):
                        print(
                            f"#{event.pipe_id} "
                            "finished rocking"
                        )

                #
                # Check stdin without blocking the scheduler.
                #
                readable, _, _ = (
                    select.select(
                        [
                            sys.stdin
                        ],
                        [],
                        [],
                        0.0,
                    )
                )

                if readable:
                    command = (
                        sys.stdin.readline()
                    )

                    if command == "":
                        break

                    if not process_command(
                        command,
                        pipes,
                    ):
                        break

                elapsed = (
                    time.monotonic()
                    - loop_start
                )

                sleep_seconds = (
                    interval
                    - elapsed
                )

                if sleep_seconds > 0:
                    time.sleep(
                        sleep_seconds
                    )

        finally:
            pipes.stop_all()

    print()
    print(
        "Multi-pipe test stopped."
    )


if __name__ == "__main__":
    main()
