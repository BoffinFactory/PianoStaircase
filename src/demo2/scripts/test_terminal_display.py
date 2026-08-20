#!/usr/bin/env python3

"""
Standalone terminal-display diagnostic for Piano Staircase Demo 2.

The diagnostic simulates sensor readings and application activity without
using any hardware.

Press Ctrl+C to stop.
"""

import math
import time

from rich.console import Console
from rich.live import Live

from piano_staircase_demo.terminal_display import (
    DisplayState,
    TerminalDisplay,
)


INTERACTION_SECONDS = 4.5

RESPONSES = (
    (
        "C4",
        "green",
        430,
    ),
    (
        "E4",
        "yellow",
        270,
    ),
    (
        "G4",
        "blue",
        110,
    ),
)

RESPONSE_MODES = (
    "cycle",
    "random",
    "distance",
)


def build_state(
    elapsed: float,
) -> DisplayState:
    """Build one simulated application state."""

    interaction_number = int(
        elapsed // INTERACTION_SECONDS
    )

    phase = (
        elapsed
        % INTERACTION_SECONDS
    )

    response_index = (
        interaction_number
        % len(RESPONSES)
    )

    (
        note,
        light_name,
        trigger_distance,
    ) = RESPONSES[
        response_index
    ]

    response_mode = RESPONSE_MODES[
        (
            interaction_number // 3
        )
        % len(RESPONSE_MODES)
    ]

    special = (
        interaction_number > 0
        and interaction_number % 7 == 6
    )

    # Idle: show a genuinely moving-looking sensor value.
    idle_distance = int(
        900
        + 90
        * math.sin(
            elapsed * 1.4
        )
    )

    if phase < 1.2:
        return DisplayState(
            distance_mm=idle_distance,
            trigger_state="ARMED",
            response_mode=response_mode,
            code_stage="sensor",
        )

    if phase < 1.5:
        progress = (
            phase - 1.2
        ) / 0.3

        distance = round(
            idle_distance
            + (
                trigger_distance
                - idle_distance
            )
            * progress
        )

        return DisplayState(
            distance_mm=distance,
            trigger_state="ARMED",
            response_mode=response_mode,
            code_stage="sensor",
        )

    if phase < 1.8:
        return DisplayState(
            distance_mm=trigger_distance,
            trigger_state="FIRED",
            response_mode=response_mode,
            code_stage="trigger",
            special_text=(
                "SPECIAL EVENT // FLOURISH"
                if special
                else None
            ),
        )

    if phase < 2.1:
        return DisplayState(
            distance_mm=trigger_distance,
            trigger_state="FIRED",
            response_mode=response_mode,
            note=note,
            light_name=light_name,
            code_stage="response",
            special_text=(
                "SPECIAL EVENT // FLOURISH"
                if special
                else None
            ),
        )

    if phase < 2.5:
        return DisplayState(
            distance_mm=trigger_distance,
            trigger_state="FIRED",
            response_mode=response_mode,
            note=note,
            light_name=light_name,
            output_active=True,
            code_stage="lighting",
            special_text=(
                "SPECIAL EVENT // FLOURISH"
                if special
                else None
            ),
        )

    if phase < 3.0:
        return DisplayState(
            distance_mm=trigger_distance,
            trigger_state="FIRED",
            response_mode=response_mode,
            note=note,
            light_name=light_name,
            output_active=True,
            audio_active=True,
            code_stage="audio",
            special_text=(
                "SPECIAL EVENT // FLOURISH"
                if special
                else None
            ),
        )

    if phase < 3.5:
        return DisplayState(
            distance_mm=trigger_distance,
            trigger_state="ARMED",
            response_mode=response_mode,
            note=note,
            light_name=light_name,
            code_stage="sensor",
        )

    return DisplayState(
        distance_mm=idle_distance,
        trigger_state="ARMED",
        response_mode=response_mode,
        code_stage="sensor",
    )


def main() -> None:
    console = Console()
    display = TerminalDisplay(
        console
    )

    start_time = time.monotonic()

    initial_state = build_state(0.0)

    try:
        with Live(
            display.render(
                initial_state,
                now_seconds=0.0,
            ),
            console=console,
            screen=True,
            auto_refresh=False,
        ) as live:
            while True:
                now = time.monotonic()
                elapsed = (
                    now - start_time
                )

                state = build_state(
                    elapsed
                )

                live.update(
                    display.render(
                        state,
                        now_seconds=elapsed,
                    ),
                    refresh=True,
                )

                time.sleep(0.10)

    except KeyboardInterrupt:
        pass

    console.print(
        "[dim]Terminal display diagnostic stopped.[/]"
    )


if __name__ == "__main__":
    main()
