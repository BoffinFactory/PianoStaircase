"""
Special-event scheduling for Piano Staircase Demo 2.

Special events periodically replace an ordinary accepted interaction with
an unusual response. They are separate from normal response selection and
from articulation behavior.
"""

from __future__ import annotations

import random


class SpecialEventDirector:
    """Periodically select a special event."""

    def __init__(
        self,
        *,
        every_n_interactions: int,
        event_names: tuple[str, ...],
    ) -> None:
        if every_n_interactions < 0:
            raise ValueError(
                "every_n_interactions cannot be negative."
            )

        if every_n_interactions > 0 and not event_names:
            raise ValueError(
                "At least one event is required when special events "
                "are enabled."
            )

        self.every_n_interactions = every_n_interactions
        self._event_names = event_names

        self._interaction_count = 0
        self._last_event_index: int | None = None

    def record_interaction(self) -> str | None:
        """
        Record one accepted interaction.

        Return the name of a selected special event when the configured
        interval is reached. Otherwise return None.
        """

        self._interaction_count += 1

        if self.every_n_interactions == 0:
            return None

        if (
            self._interaction_count
            % self.every_n_interactions
            != 0
        ):
            return None

        if len(self._event_names) == 1:
            index = 0

        else:
            available_indices = [
                index
                for index in range(len(self._event_names))
                if index != self._last_event_index
            ]

            index = random.choice(available_indices)

        self._last_event_index = index

        return self._event_names[index]


class TemporaryEventOverride:
    """Temporarily replace ordinary interactions with one special event."""

    def __init__(self) -> None:
        self._event_name: str | None = None
        self._remaining_interactions = 0

    @property
    def active(self) -> bool:
        """Return True while an override is active."""

        return self._event_name is not None

    @property
    def event_name(self) -> str | None:
        """Return the active event name, if any."""

        return self._event_name

    @property
    def remaining_interactions(self) -> int:
        """Return how many accepted interactions remain."""

        return self._remaining_interactions

    def activate(
        self,
        event_name: str,
        *,
        interactions: int,
    ) -> None:
        """Activate an event override for a fixed number of interactions."""

        if not event_name:
            raise ValueError(
                "event_name cannot be empty."
            )

        if interactions < 1:
            raise ValueError(
                "interactions must be at least 1."
            )

        if self.active:
            raise RuntimeError(
                "A temporary event override is already active."
            )

        self._event_name = event_name
        self._remaining_interactions = interactions

    def consume(self) -> str | None:
        """
        Consume one accepted interaction from the active override.

        Return the active event name, or None when no override is active.
        """

        if not self.active:
            return None

        assert self._event_name is not None

        event_name = self._event_name

        self._remaining_interactions -= 1

        if self._remaining_interactions == 0:
            self._event_name = None

        return event_name
