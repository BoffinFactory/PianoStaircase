"""Stable hysteretic distance zones for Piano Staircase Demo 2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneTransition:
    """One accepted change between stable distance zones."""

    previous_zone: int | None
    current_zone: int | None


class DistanceZoneTracker:
    """
    Divide one sensor span into stable distance zones.

    Zone indices are ordered from farthest to closest. With the normal
    three-zone configuration this means:

        0 -> GREEN / C4
        1 -> YELLOW / E4
        2 -> BLUE / G4

    Internal boundaries use hysteresis and every transition requires several
    consecutive confirming samples. Leaving the far edge has its own debounce.
    """

    def __init__(
        self,
        *,
        near_distance_mm: int,
        far_distance_mm: int,
        zone_count: int = 3,
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
        if zone_count < 2:
            raise ValueError("zone_count must be at least 2.")
        if hysteresis_mm < 0:
            raise ValueError("hysteresis_mm cannot be negative.")
        if transition_samples < 1:
            raise ValueError("transition_samples must be at least 1.")
        if exit_samples < 1:
            raise ValueError("exit_samples must be at least 1.")

        self.near_distance_mm = near_distance_mm
        self.far_distance_mm = far_distance_mm
        self.zone_count = zone_count
        self.hysteresis_mm = hysteresis_mm
        self.transition_samples = transition_samples
        self.exit_samples = exit_samples

        self._zone_width_mm = (
            far_distance_mm - near_distance_mm
        ) / zone_count

        if 2 * hysteresis_mm >= self._zone_width_mm:
            raise ValueError(
                "hysteresis is too large for the configured zone width."
            )

        self._current_zone: int | None = None
        self._candidate_zone: int | None = None
        self._candidate_samples = 0

    @property
    def current_zone(self) -> int | None:
        """Return the currently accepted stable zone."""

        return self._current_zone

    @property
    def zone_width_mm(self) -> float:
        """Return the nominal physical width of one zone."""

        return self._zone_width_mm

    @property
    def boundaries_mm(self) -> tuple[int, ...]:
        """Return nominal internal boundaries from near to far."""

        return tuple(
            round(
                self.near_distance_mm
                + self._zone_width_mm * boundary_number
            )
            for boundary_number in range(1, self.zone_count)
        )

    def _nominal_zone(self, distance_mm: int) -> int | None:
        """Return the non-hysteretic zone for one measurement."""

        if distance_mm > self.far_distance_mm:
            return None

        clamped_distance = max(self.near_distance_mm, distance_mm)
        position = (
            self.far_distance_mm - clamped_distance
        ) / (
            self.far_distance_mm - self.near_distance_mm
        )

        zone = int(position * self.zone_count)
        return min(zone, self.zone_count - 1)

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

        # Moving closer means moving to a larger zone index. The measurement
        # must pass the nominal boundary by hysteresis_mm before it counts.
        if nominal_zone > self._current_zone:
            boundary_mm = (
                self.far_distance_mm
                - self._zone_width_mm * (self._current_zone + 1)
            )

            if distance_mm <= boundary_mm - self.hysteresis_mm:
                return nominal_zone

            return self._current_zone

        # Moving farther means moving to a smaller zone index.
        boundary_mm = (
            self.far_distance_mm
            - self._zone_width_mm * self._current_zone
        )

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
