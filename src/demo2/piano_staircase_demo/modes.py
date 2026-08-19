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
