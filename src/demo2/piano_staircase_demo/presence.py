"""
Presence tracking for Piano Staircase Demo 2.

This module converts valid distance measurements into sustained interaction
events suitable for instrument-style behavior:

    ENTER
        An object has newly entered the active sensor region.

    HELD
        The object remains present.

    EXIT
        The object has moved far enough away to release the interaction.

When no object is present and no transition occurs, update() returns None.

The tracker contains no Raspberry Pi or sensor-specific code.
"""

from __future__ import annotations

from enum import Enum


class PresenceEvent(Enum):
    """One semantic change/state in a sustained proximity interaction."""

    ENTER = "ENTER"
    HELD = "HELD"
    EXIT = "EXIT"


class PresenceTracker:
    """
    Convert distance measurements into ENTER / HELD / EXIT behavior.

    Separate enter and exit distances provide hysteresis so small movements
    near the trigger boundary do not repeatedly start and stop an interaction.
    """

    def __init__(
        self,
        *,
        enter_distance_mm: int,
        exit_distance_mm: int,
        enter_samples: int = 1,
        exit_samples: int = 1,
    ) -> None:
        if enter_distance_mm <= 0:
            raise ValueError(
                "enter_distance_mm must be greater than zero."
            )

        if exit_distance_mm <= enter_distance_mm:
            raise ValueError(
                "exit_distance_mm must be greater than "
                "enter_distance_mm."
            )

        if enter_samples < 1:
            raise ValueError(
                "enter_samples must be at least 1."
            )

        if exit_samples < 1:
            raise ValueError(
                "exit_samples must be at least 1."
            )

        self.enter_distance_mm = (
            enter_distance_mm
        )

        self.exit_distance_mm = (
            exit_distance_mm
        )

        self.enter_samples = (
            enter_samples
        )

        self.exit_samples = (
            exit_samples
        )

        self._present = False

        self._enter_count = 0
        self._exit_count = 0

    @property
    def present(
        self,
    ) -> bool:
        """Return True while an object is considered present."""

        return self._present

    def reset(
        self,
    ) -> None:
        """Return the tracker to its initial absent state."""

        self._present = False

        self._enter_count = 0
        self._exit_count = 0

    def update(
        self,
        distance_mm: int,
    ) -> PresenceEvent | None:
        """
        Process one valid distance measurement.

        Invalid sensor samples should be ignored by the caller rather than
        passed here. Ignoring them preserves the current presence state.
        """

        if distance_mm < 0:
            raise ValueError(
                "distance_mm cannot be negative."
            )

        # ---------------------------------------------------------------
        # Nothing is currently present.
        # ---------------------------------------------------------------

        if not self._present:
            self._exit_count = 0

            if (
                distance_mm
                <= self.enter_distance_mm
            ):
                self._enter_count += 1

            else:
                self._enter_count = 0

            if (
                self._enter_count
                >= self.enter_samples
            ):
                self._present = True
                self._enter_count = 0

                return PresenceEvent.ENTER

            return None

        # ---------------------------------------------------------------
        # An object is currently present.
        # ---------------------------------------------------------------

        self._enter_count = 0

        if (
            distance_mm
            >= self.exit_distance_mm
        ):
            self._exit_count += 1

        else:
            self._exit_count = 0

        if (
            self._exit_count
            >= self.exit_samples
        ):
            self._present = False
            self._exit_count = 0

            return PresenceEvent.EXIT

        return PresenceEvent.HELD
