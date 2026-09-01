"""
Reusable interaction-control logic for Piano Staircase Demo 2.

This module contains hardware-independent policies that control how often
physical interactions may produce application actions.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time

from piano_staircase_demo.zones import ZoneTransition


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


@dataclass(frozen=True)
class RapidPlayStatus:
    """Display-friendly snapshot of the rapid-play detector."""

    active: bool
    movement_count: int
    reversal_count: int
    seconds_remaining: float | None


@dataclass(frozen=True)
class RapidPlayUpdate:
    """Result of observing one accepted stable zone transition."""

    active: bool
    activated: bool
    reversal: bool
    movement_count: int
    reversal_count: int
    seconds_remaining: float | None


class RapidPlayDetector:
    """
    Detect deliberate rapid back-and-forth movement across stable zones.

    The detector intentionally consumes already-debounced ZoneTransition
    objects rather than raw sensor samples. A simple approach-and-retreat may
    cross many zones but usually contains only one direction reversal, while
    deliberate waving produces repeated reversals in a short rolling window.

    Once active, any accepted zone transition refreshes the inactivity timer.
    Additional pipe responses may be rate-limited with allow_pipe_spawn().
    """

    def __init__(
        self,
        *,
        window_seconds: float,
        required_movements: int,
        required_reversals: int,
        idle_timeout_seconds: float,
        pipe_spawn_cooldown_seconds: float,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero.")
        if required_movements < 2:
            raise ValueError("required_movements must be at least 2.")
        if required_reversals < 1:
            raise ValueError("required_reversals must be at least 1.")
        if required_reversals >= required_movements:
            raise ValueError(
                "required_reversals must be less than required_movements."
            )
        if idle_timeout_seconds <= 0:
            raise ValueError(
                "idle_timeout_seconds must be greater than zero."
            )
        if pipe_spawn_cooldown_seconds < 0:
            raise ValueError(
                "pipe_spawn_cooldown_seconds cannot be negative."
            )

        self.window_seconds = window_seconds
        self.required_movements = required_movements
        self.required_reversals = required_reversals
        self.idle_timeout_seconds = idle_timeout_seconds
        self.pipe_spawn_cooldown_seconds = pipe_spawn_cooldown_seconds

        # Each tuple is (accepted_time, direction), where +1 means the hand
        # moved closer and -1 means it moved farther.
        self._movements: deque[tuple[float, int]] = deque()

        self._active = False
        self._last_activity_time: float | None = None
        self._last_active_direction: int | None = None
        self._last_pipe_spawn_time: float | None = None

    @property
    def active(self) -> bool:
        """Return whether Pipe Physics Mode is currently active."""

        return self._active

    @staticmethod
    def _movement_direction(
        transition: ZoneTransition,
    ) -> int | None:
        """Return +1 closer, -1 farther, or None for entry/exit."""

        if (
            transition.previous_zone is None
            or transition.current_zone is None
        ):
            return None

        if transition.current_zone > transition.previous_zone:
            return 1

        if transition.current_zone < transition.previous_zone:
            return -1

        return None

    def _prune(self, now: float) -> None:
        """Remove movement samples outside the rolling activation window."""

        cutoff = now - self.window_seconds

        while self._movements and self._movements[0][0] < cutoff:
            self._movements.popleft()

    def _reversal_count(self) -> int:
        """Count direction changes in the current rolling movement window."""

        directions = [direction for _, direction in self._movements]

        return sum(
            current != previous
            for previous, current in zip(directions, directions[1:])
        )

    def _progress(self, now: float) -> tuple[int, int]:
        """Return current rolling movement/reversal progress."""

        self._prune(now)
        return len(self._movements), self._reversal_count()

    def seconds_until_idle(self, *, now: float | None = None) -> float | None:
        """Return seconds until active mode expires, or None while inactive."""

        if not self._active or self._last_activity_time is None:
            return None

        if now is None:
            now = time.monotonic()

        return max(
            0.0,
            self.idle_timeout_seconds - (now - self._last_activity_time),
        )

    def snapshot(self, *, now: float | None = None) -> RapidPlayStatus:
        """Return current detector state without changing activation state."""

        if now is None:
            now = time.monotonic()

        movements, reversals = self._progress(now)

        return RapidPlayStatus(
            active=self._active,
            movement_count=movements,
            reversal_count=reversals,
            seconds_remaining=self.seconds_until_idle(now=now),
        )

    def reset(self) -> None:
        """Return the detector to its initial inactive state."""

        self._movements.clear()
        self._active = False
        self._last_activity_time = None
        self._last_active_direction = None
        self._last_pipe_spawn_time = None

    def service(self, *, now: float | None = None) -> bool:
        """
        Expire active mode after inactivity.

        Return True only when this call actually deactivates Pipe Physics Mode.
        """

        if now is None:
            now = time.monotonic()

        self._prune(now)

        if not self._active or self._last_activity_time is None:
            return False

        if now - self._last_activity_time < self.idle_timeout_seconds:
            return False

        self._active = False
        self._movements.clear()
        self._last_activity_time = None
        self._last_active_direction = None
        self._last_pipe_spawn_time = None
        return True

    def observe_transition(
        self,
        transition: ZoneTransition,
        *,
        now: float | None = None,
    ) -> RapidPlayUpdate:
        """Observe one accepted stable zone transition."""

        if now is None:
            now = time.monotonic()

        # A movement arriving after a long pause begins a fresh interaction
        # rather than resurrecting the previous Pipe Physics session.
        self.service(now=now)

        direction = self._movement_direction(transition)

        if self._active:
            self._last_activity_time = now

            reversal = False

            if direction is None:
                # Entry/exit still counts as activity, but the first movement
                # after re-entry should establish a new direction rather than
                # compare against stale motion from before leaving the range.
                self._last_active_direction = None
            else:
                reversal = (
                    self._last_active_direction is not None
                    and direction != self._last_active_direction
                )
                self._last_active_direction = direction

            movements, reversals = self._progress(now)

            return RapidPlayUpdate(
                active=True,
                activated=False,
                reversal=reversal,
                movement_count=movements,
                reversal_count=reversals,
                seconds_remaining=self.seconds_until_idle(now=now),
            )

        if direction is not None:
            self._movements.append((now, direction))

        movements, reversals = self._progress(now)

        activated = (
            movements >= self.required_movements
            and reversals >= self.required_reversals
        )

        if activated:
            self._active = True
            self._last_activity_time = now
            self._last_active_direction = direction

        return RapidPlayUpdate(
            active=self._active,
            activated=activated,
            reversal=False,
            movement_count=movements,
            reversal_count=reversals,
            seconds_remaining=self.seconds_until_idle(now=now),
        )

    def allow_pipe_spawn(self, *, now: float | None = None) -> bool:
        """Rate-limit newly launched pipes while Pipe Physics Mode is active."""

        if not self._active:
            return False

        if now is None:
            now = time.monotonic()

        if self._last_pipe_spawn_time is None:
            self._last_pipe_spawn_time = now
            return True

        if (
            now - self._last_pipe_spawn_time
            < self.pipe_spawn_cooldown_seconds
        ):
            return False

        self._last_pipe_spawn_time = now
        return True
