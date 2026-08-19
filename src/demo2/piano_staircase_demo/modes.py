"""
Response-selection modes for Piano Staircase Demo 2.

Response modes decide which musical and lighting response should be used
for an interaction. They do not decide when an interaction begins or ends,
how long a note is sustained, or directly control hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class InteractionResponse:
    """One musical and lighting response chosen by an interaction mode."""

    note: str
    light_name: str


class CycleMode:
    """Cycle through a fixed sequence of note/light responses."""

    def __init__(
        self,
        responses: tuple[InteractionResponse, ...],
    ) -> None:
        if not responses:
            raise ValueError(
                "CycleMode requires at least one response."
            )

        self._responses = responses
        self._next_index = 0

    def next_response(
        self,
        distance_mm: int | None = None,
    ) -> InteractionResponse:
        """
        Return the next response in the cycle.

        distance_mm is accepted so that interaction modes share a useful
        interface. CycleMode does not currently use the distance value.
        """

        response = self._responses[self._next_index]

        self._next_index = (
            self._next_index + 1
        ) % len(self._responses)

        return response


class RandomMode:
    """Choose responses randomly without immediately repeating one."""

    def __init__(
        self,
        responses: tuple[InteractionResponse, ...],
    ) -> None:
        if not responses:
            raise ValueError(
                "RandomMode requires at least one response."
            )

        self._responses = responses
        self._last_index: int | None = None

    def next_response(
        self,
        distance_mm: int | None = None,
    ) -> InteractionResponse:
        """
        Return a randomly selected response.

        When more than one response is available, the immediately previous
        response is excluded so repeated interactions do not produce the
        same response twice in a row.

        distance_mm is accepted so that response modes share a useful
        interface. RandomMode does not currently use the distance value.
        """

        if len(self._responses) == 1:
            return self._responses[0]

        available_indices = [
            index
            for index in range(len(self._responses))
            if index != self._last_index
        ]

        index = random.choice(available_indices)
        self._last_index = index

        return self._responses[index]


class DistanceMode:
    """
    Select a response based on measured distance.

    Responses are ordered from lowest/farthest to highest/closest.
    The configured distance range is divided evenly among them.
    """

    def __init__(
        self,
        responses: tuple[InteractionResponse, ...],
        *,
        minimum_distance_mm: int,
        maximum_distance_mm: int,
    ) -> None:
        if not responses:
            raise ValueError(
                "DistanceMode requires at least one response."
            )

        if minimum_distance_mm < 0:
            raise ValueError(
                "minimum_distance_mm cannot be negative."
            )

        if maximum_distance_mm <= minimum_distance_mm:
            raise ValueError(
                "maximum_distance_mm must be greater than "
                "minimum_distance_mm."
            )

        self._responses = responses
        self.minimum_distance_mm = minimum_distance_mm
        self.maximum_distance_mm = maximum_distance_mm

    def next_response(
        self,
        distance_mm: int | None = None,
    ) -> InteractionResponse:
        """
        Return the response corresponding to the measured distance.

        Closer measurements select responses later in the sequence.
        Farther measurements select responses earlier in the sequence.
        """

        if distance_mm is None:
            raise ValueError(
                "DistanceMode requires a distance measurement."
            )

        # Clamp measurements to the configured range.
        distance_mm = max(
            self.minimum_distance_mm,
            min(distance_mm, self.maximum_distance_mm),
        )

        distance_range = (
            self.maximum_distance_mm
            - self.minimum_distance_mm
        )

        normalized_distance = (
            distance_mm - self.minimum_distance_mm
        ) / distance_range

        band = int(
            normalized_distance
            * len(self._responses)
        )

        # The exact maximum distance would otherwise produce an index
        # one past the end of the tuple.
        band = min(
            band,
            len(self._responses) - 1,
        )

        index = (
            len(self._responses)
            - 1
            - band
        )

        return self._responses[index]
