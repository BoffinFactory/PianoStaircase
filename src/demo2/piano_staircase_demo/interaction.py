"""
Reusable interaction-control logic for Piano Staircase Demo 2.

This module contains hardware-independent policies that control how often physical interactions may
produce application actions.
"""

from __future__ import annotations

import time


class CooldownGate:
    """Limit how often an action may be accepted."""

    def __init__(self, minimum_interval_seconds: float) -> None:
        if minimum_interval_seconds < 0:
            raise ValueError(
                "minimum_interval_seconds cannot be negative."
            )

        self.minimum_interval_seconds = minimum_interval_seconds
        self._last_accepted_time: float | None = None

    def allow(self) -> bool:
        """Return True if an action may occur now."""

        now = time.monotonic()

        if self._last_accepted_time is None:
            self._last_accepted_time = now
            return True

        elapsed = now - self._last_accepted_time

        if elapsed < self.minimum_interval_seconds:
            return False

        self._last_accepted_time = now
        return True
