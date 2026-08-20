"""
Separate-process support for the Demo 2 terminal presentation.

Rich terminal rendering can require significant CPU time. Running the
presentation in its own process keeps that work out of the timing-sensitive
hardware control loop.

The hardware process publishes small DisplayState snapshots. Only the newest
snapshot matters; stale snapshots are deliberately discarded rather than
queued for later rendering.
"""

from __future__ import annotations

import multiprocessing
import queue
import signal
import time
from typing import Any

from rich.console import Console
from rich.live import Live

from piano_staircase_demo.terminal_display import (
    DisplayState,
    TerminalDisplay,
)


def _offer_latest(
    queue_object: Any,
    value: object,
) -> None:
    """
    Put a value into a one-item multiprocessing queue without blocking.

    If the queue already contains an older value, discard that stale value
    and try to replace it with the newest one.
    """

    try:
        queue_object.put_nowait(value)
        return

    except queue.Full:
        pass

    try:
        queue_object.get_nowait()

    except queue.Empty:
        pass

    try:
        queue_object.put_nowait(value)

    except queue.Full:
        # Another queue operation won the race. A display frame is allowed
        # to be dropped; the hardware process must never wait for it.
        pass


def _get_latest(
    queue_object: Any,
    current_value: DisplayState,
) -> DisplayState:
    """Drain pending states and return the newest available one."""

    latest = current_value

    while True:
        try:
            latest = queue_object.get_nowait()

        except queue.Empty:
            return latest


def _display_worker(
    state_queue: Any,
    error_queue: Any,
    stop_event: Any,
    initial_state: DisplayState,
    refresh_hz: float,
) -> None:
    """
    Run the Rich display in a child process.

    This function must remain at module scope so Python's multiprocessing
    "spawn" start method can import it in the new process.
    """

    # Ctrl+C belongs to the main hardware process. The parent will ask this
    # process to stop cleanly after it handles the signal.
    signal.signal(
        signal.SIGINT,
        signal.SIG_IGN,
    )

    try:
        console = Console()
        display = TerminalDisplay(console)

        latest_state = initial_state

        refresh_interval = (
            1.0 / refresh_hz
        )

        start_time = time.monotonic()
        next_frame = start_time

        with Live(
            display.render(
                latest_state,
                now_seconds=0.0,
            ),
            console=console,
            screen=True,
            auto_refresh=False,
        ) as live:

            while not stop_event.is_set():
                # Always throw away stale states and keep the newest one.
                latest_state = _get_latest(
                    state_queue,
                    latest_state,
                )

                now = time.monotonic()

                if now >= next_frame:
                    live.update(
                        display.render(
                            latest_state,
                            now_seconds=(
                                now - start_time
                            ),
                        ),
                        refresh=True,
                    )

                    next_frame = (
                        now + refresh_interval
                    )

                # Wake frequently enough for a quick clean shutdown, but do
                # not busy-spin between display frames.
                wait_seconds = max(
                    0.0,
                    min(
                        next_frame - time.monotonic(),
                        0.05,
                    ),
                )

                stop_event.wait(
                    wait_seconds
                )

    except Exception as exc:
        _offer_latest(
            error_queue,
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )


class DisplayProcess:
    """
    Manage the optional terminal presentation process.

    The public interface is intentionally tiny:

        display = DisplayProcess.start(...)
        display.publish(state)
        display.close()

    The caller does not need to know anything about multiprocessing queues
    or Rich's Live display.
    """

    def __init__(
        self,
        *,
        process: Any,
        state_queue: Any,
        error_queue: Any,
        stop_event: Any,
    ) -> None:
        self._process = process
        self._state_queue = state_queue
        self._error_queue = error_queue
        self._stop_event = stop_event

        self._closed = False

    @classmethod
    def start(
        cls,
        *,
        initial_state: DisplayState,
        refresh_hz: float = 5.0,
    ) -> DisplayProcess:
        """Start a terminal display in a clean spawned process."""

        if refresh_hz <= 0:
            raise ValueError(
                "refresh_hz must be greater than zero."
            )

        # Explicitly use spawn rather than Linux's normal fork behavior.
        # That prevents the display process from inheriting active I2C/GPIO
        # resources from the hardware process.
        context = multiprocessing.get_context(
            "spawn"
        )

        state_queue = context.Queue(
            maxsize=1
        )

        error_queue = context.Queue(
            maxsize=1
        )

        stop_event = context.Event()

        process = context.Process(
            target=_display_worker,
            args=(
                state_queue,
                error_queue,
                stop_event,
                initial_state,
                refresh_hz,
            ),
            name="piano-demo-display",
            daemon=True,
        )

        process.start()

        return cls(
            process=process,
            state_queue=state_queue,
            error_queue=error_queue,
            stop_event=stop_event,
        )

    @property
    def is_alive(self) -> bool:
        """Return whether the child display process is still running."""

        return (
            not self._closed
            and self._process.is_alive()
        )

    def publish(
        self,
        state: DisplayState,
    ) -> bool:
        """
        Publish the newest presentation state without blocking.

        Returns False if the display process is no longer running.
        """

        if not self.is_alive:
            return False

        try:
            _offer_latest(
                self._state_queue,
                state,
            )

        except (
            OSError,
            ValueError,
        ):
            return False

        return self.is_alive

    def error_message(
        self,
    ) -> str | None:
        """Return a child-process error message if one is available."""

        try:
            return self._error_queue.get_nowait()

        except queue.Empty:
            return None

        except (
            OSError,
            ValueError,
        ):
            return None

    def close(self) -> None:
        """Ask the display process to stop and clean up its IPC resources."""

        if self._closed:
            return

        self._closed = True

        self._stop_event.set()

        self._process.join(
            timeout=2.0
        )

        if self._process.is_alive:
            self._process.terminate()

            self._process.join(
                timeout=1.0
            )

        for queue_object in (
            self._state_queue,
            self._error_queue,
        ):
            try:
                queue_object.cancel_join_thread()
                queue_object.close()

            except (
                OSError,
                ValueError,
            ):
                pass

    def __enter__(
        self,
    ) -> DisplayProcess:
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
