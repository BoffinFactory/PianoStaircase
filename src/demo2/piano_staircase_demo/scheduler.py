"""Cooperative scheduler timing helpers for Piano Staircase Demo 2."""

from __future__ import annotations

import time

from piano_staircase_demo.pipes import PipeSystem


PIPE_UPDATE_HZ = 200.0


def advance_sample_schedule(
    *,
    next_sample: float,
    interval: float,
) -> float:
    """Schedule the next sensor poll without catch-up bursts."""

    next_sample += interval
    now = time.monotonic()

    if next_sample < now - interval:
        return now + interval

    return next_sample


def service_pipe_system(
    pipes: PipeSystem | None,
    *,
    now: float,
) -> None:
    """Advance procedural pipe physics without blocking the hardware loop."""

    if pipes is not None:
        pipes.update(now=now)


def sleep_until_next_work(
    *,
    next_sample: float,
    pipes: PipeSystem | None,
) -> None:
    """Sleep until sensor work or an active pipe needs another scheduler tick."""

    now = time.monotonic()
    sleep_seconds = max(0.0, next_sample - now)

    if pipes is not None and pipes.active_count > 0:
        sleep_seconds = min(sleep_seconds, 1.0 / PIPE_UPDATE_HZ)

    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
