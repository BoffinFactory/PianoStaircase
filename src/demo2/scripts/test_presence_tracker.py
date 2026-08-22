#!/usr/bin/env python3

"""
Exercise the Demo 2 sustained-presence tracker.

This test uses simulated distance readings so ENTER / HELD / EXIT behavior
can be verified without Raspberry Pi hardware.
"""

from __future__ import annotations

from piano_staircase_demo.presence import (
    PresenceEvent,
    PresenceTracker,
)


ENTER_DISTANCE_MM = 500
EXIT_DISTANCE_MM = 750


def describe_event(
    event: PresenceEvent | None,
) -> str:
    """Return a friendly printable event name."""

    if event is None:
        return "—"

    return event.value


def main(
) -> None:
    """Run deterministic presence-tracking scenarios."""

    tracker = PresenceTracker(
        enter_distance_mm=(
            ENTER_DISTANCE_MM
        ),
        exit_distance_mm=(
            EXIT_DISTANCE_MM
        ),
        enter_samples=1,
        exit_samples=1,
    )

    #
    # Each tuple contains:
    #
    #     distance
    #     expected event
    #
    # The sequence deliberately crosses both thresholds and spends time
    # inside the hysteresis region between them.
    #
    samples = (
        (900, None),
        (800, None),
        (600, None),

        # Enter active region.
        (480, PresenceEvent.ENTER),

        # Stay close.
        (450, PresenceEvent.HELD),
        (470, PresenceEvent.HELD),

        # Move outside the ENTER threshold but remain inside the EXIT
        # threshold. Presence should remain held.
        (520, PresenceEvent.HELD),
        (650, PresenceEvent.HELD),
        (720, PresenceEvent.HELD),

        # Cross the release threshold.
        (760, PresenceEvent.EXIT),

        # Now absent again.
        (700, None),
        (600, None),

        # A second interaction should work normally.
        (490, PresenceEvent.ENTER),
        (400, PresenceEvent.HELD),
        (800, PresenceEvent.EXIT),

        # Remain absent.
        (900, None),
    )

    print(
        "=== PresenceTracker test ==="
    )

    print()

    print(
        "Enter distance: "
        f"{ENTER_DISTANCE_MM} mm"
    )

    print(
        "Exit distance:  "
        f"{EXIT_DISTANCE_MM} mm"
    )

    print()

    print(
        " distance | expected | actual   | present"
    )

    print(
        "----------+----------+----------+--------"
    )

    for (
        distance_mm,
        expected,
    ) in samples:
        actual = tracker.update(
            distance_mm
        )

        status = (
            "PASS"
            if actual is expected
            else "FAIL"
        )

        print(
            f"{distance_mm:8d} "
            f"| {describe_event(expected):8s} "
            f"| {describe_event(actual):8s} "
            f"| {str(tracker.present):7s} "
            f"{status}"
        )

        if actual is not expected:
            raise AssertionError(
                "PresenceTracker produced "
                "an unexpected event."
            )

    print()
    print(
        "All presence-tracking tests passed."
    )


if __name__ == "__main__":
    main()
