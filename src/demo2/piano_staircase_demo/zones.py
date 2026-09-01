"""Stable hysteretic distance zones for Piano Staircase Demo 2."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneTransition:
    """One accepted change between stable distance zones."""

    previous_zone: int | None
    current_zone: int | None


class DistanceZoneTracker:
    """
    Divide one sensor span into stable distance zones.

    Zone indices are ordered from farthest to closest. Callers may either
    request evenly sized zones with zone_count (legacy behavior), or provide
    explicit boundaries_mm ordered from nearest to farthest for a nonlinear
    physical layout.

    Internal boundaries use hysteresis and every transition requires several
    consecutive confirming samples. Leaving the far edge has its own debounce.
    """

    def __init__(
        self,
        *,
        near_distance_mm: int,
        far_distance_mm: int,
        zone_count: int = 3,
        boundaries_mm: tuple[int, ...] | None = None,
        hysteresis_mm: int = 50,
        transition_samples: int = 3,
        exit_samples: int = 3,
    ) -> None:
        if near_distance_mm <= 0:
            raise ValueError("near_distance_mm must be greater than zero.")
        if far_distance_mm <= near_distance_mm:
            raise ValueError(
                "far_distance_mm must be greater than near_distance_mm."
            )
        if hysteresis_mm < 0:
            raise ValueError("hysteresis_mm cannot be negative.")
        if transition_samples < 1:
            raise ValueError("transition_samples must be at least 1.")
        if exit_samples < 1:
            raise ValueError("exit_samples must be at least 1.")

        if boundaries_mm is None:
            if zone_count < 2:
                raise ValueError("zone_count must be at least 2.")

            zone_width = (
                far_distance_mm - near_distance_mm
            ) / zone_count

            boundaries_mm = tuple(
                round(near_distance_mm + zone_width * boundary_number)
                for boundary_number in range(1, zone_count)
            )
        else:
            boundaries_mm = tuple(boundaries_mm)
            zone_count = len(boundaries_mm) + 1

        if not boundaries_mm:
            raise ValueError(
                "At least one internal zone boundary is required.")
        if tuple(sorted(boundaries_mm)) != boundaries_mm:
            raise ValueError("boundaries_mm must be strictly increasing.")
        if len(set(boundaries_mm)) != len(boundaries_mm):
            raise ValueError("boundaries_mm cannot contain duplicates.")
        if boundaries_mm[0] <= near_distance_mm:
            raise ValueError(
                "The nearest boundary must be greater than near_distance_mm."
            )
        if boundaries_mm[-1] >= far_distance_mm:
            raise ValueError(
                "The farthest boundary must be less than far_distance_mm."
            )

        zone_edges = (
            near_distance_mm,
            *boundaries_mm,
            far_distance_mm,
        )
        zone_widths = tuple(
            right - left
            for left, right in zip(zone_edges, zone_edges[1:])
        )

        if any(width <= 2 * hysteresis_mm for width in zone_widths):
            raise ValueError(
                "hysteresis is too large for at least one configured zone."
            )

        self.near_distance_mm = near_distance_mm
        self.far_distance_mm = far_distance_mm
        self.zone_count = zone_count
        self.hysteresis_mm = hysteresis_mm
        self.transition_samples = transition_samples
        self.exit_samples = exit_samples

        self._boundaries_mm = boundaries_mm
        self._zone_width_mm = (
            far_distance_mm - near_distance_mm
        ) / zone_count

        self._current_zone: int | None = None
        self._candidate_zone: int | None = None
        self._candidate_samples = 0

    @property
    def current_zone(self) -> int | None:
        """Return the currently accepted stable zone."""

        return self._current_zone

    @property
    def zone_width_mm(self) -> float:
        """Return the average physical width of the configured zones."""

        return self._zone_width_mm

    @property
    def boundaries_mm(self) -> tuple[int, ...]:
        """Return internal boundaries ordered from nearest to farthest."""

        return self._boundaries_mm

    def _nominal_zone(self, distance_mm: int) -> int | None:
        """Return the non-hysteretic zone for one measurement."""

        if distance_mm > self.far_distance_mm:
            return None

        clamped_distance = max(self.near_distance_mm, distance_mm)
        near_index = bisect_right(self._boundaries_mm, clamped_distance)

        return self.zone_count - 1 - near_index

    def _desired_zone(self, distance_mm: int) -> int | None:
        """Return the candidate zone after boundary hysteresis."""

        if distance_mm > self.far_distance_mm:
            return None

        nominal_zone = self._nominal_zone(distance_mm)
        assert nominal_zone is not None

        if self._current_zone is None:
            return nominal_zone

        if nominal_zone == self._current_zone:
            return self._current_zone

        # Moving closer means moving to a larger zone index. Require the
        # reading to pass the boundary immediately below the current zone by
        # hysteresis_mm. A fast hand may legitimately skip multiple zones.
        if nominal_zone > self._current_zone:
            boundary_index = self.zone_count - 2 - self._current_zone
            boundary_mm = self._boundaries_mm[boundary_index]

            if distance_mm <= boundary_mm - self.hysteresis_mm:
                return nominal_zone

            return self._current_zone

        # Moving farther means moving to a smaller zone index. Require the
        # reading to pass the boundary immediately above the current zone.
        boundary_index = self.zone_count - 1 - self._current_zone
        boundary_mm = self._boundaries_mm[boundary_index]

        if distance_mm >= boundary_mm + self.hysteresis_mm:
            return nominal_zone

        return self._current_zone

    def _reset_candidate(self) -> None:
        """Discard a pending transition."""

        self._candidate_zone = None
        self._candidate_samples = 0

    def reset(self) -> None:
        """Return to the initial outside-range state."""

        self._current_zone = None
        self._reset_candidate()

    def update(self, distance_mm: int) -> ZoneTransition | None:
        """
        Process one valid sensor sample.

        Return a ZoneTransition only when a new stable zone or stable EXIT has
        actually been accepted.
        """

        if distance_mm < 0:
            raise ValueError("distance_mm cannot be negative.")

        desired_zone = self._desired_zone(distance_mm)

        if self._current_zone is None and desired_zone is None:
            self._reset_candidate()
            return None

        if desired_zone == self._current_zone:
            self._reset_candidate()
            return None

        if desired_zone != self._candidate_zone:
            self._candidate_zone = desired_zone
            self._candidate_samples = 1
        else:
            self._candidate_samples += 1

        required_samples = (
            self.exit_samples
            if desired_zone is None
            else self.transition_samples
        )

        if self._candidate_samples < required_samples:
            return None

        previous_zone = self._current_zone
        self._current_zone = desired_zone
        self._reset_candidate()

        return ZoneTransition(
            previous_zone=previous_zone,
            current_zone=desired_zone,
        )
