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
