"""
Reusable trigger/rearm logic for Piano Staircase Demo 2.

This module converts raw distance measurements into one-shot proximity trigger events. It contains
no Raspberry Pi or sensor-specific code.
"""

from __future__ import annotations


class DistanceTrigger:
    """Convert distance measurements into debounced one-shot triggers."""

    def __init__(
        self,
        *,
        trigger_distance_mm: int,
        rearm_distance_mm: int,
        trigger_samples: int = 2,
        rearm_samples: int = 3,
    ) -> None:
        if trigger_distance_mm <= 0:
            raise ValueError("trigger_distance_mm must be greater than zero.")

        if rearm_distance_mm <= trigger_distance_mm:
            raise ValueError(
                "rearm_distance_mm must be greater than trigger_distance_mm."
            )

        if trigger_samples < 1:
            raise ValueError("trigger_samples must be at least 1.")

        if rearm_samples < 1:
            raise ValueError("rearm_samples must be at least 1.")

        self.trigger_distance_mm = trigger_distance_mm
        self.rearm_distance_mm = rearm_distance_mm
        self.trigger_samples = trigger_samples
        self.rearm_samples = rearm_samples

        self._armed = True
        self._trigger_count = 0
        self._rearm_count = 0

    @property
    def armed(self) -> bool:
        """Return True when the trigger is ready to fire."""

        return self._armed

    def update(self, distance_mm: int) -> bool:
        """
        Process one distance measurement.

        Return True exactly once when a confirmed trigger occurs.
        """

        if distance_mm < 0:
            raise ValueError("distance_mm cannot be negative.")

        if self._armed:
            self._rearm_count = 0

            if distance_mm <= self.trigger_distance_mm:
                self._trigger_count += 1
            else:
                self._trigger_count = 0

            if self._trigger_count >= self.trigger_samples:
                self._armed = False
                self._trigger_count = 0
                return True

        else:
            self._trigger_count = 0

            if distance_mm >= self.rearm_distance_mm:
                self._rearm_count += 1
            else:
                self._rearm_count = 0

            if self._rearm_count >= self.rearm_samples:
                self._armed = True
                self._rearm_count = 0

        return False
