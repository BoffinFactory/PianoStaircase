"""
Terminal presentation display for Piano Staircase Demo 2.

The display turns application state into a colorful terminal interface
designed to be understandable to visitors while remaining usable over SSH.

It does not control sensors, lighting, audio, or interaction behavior.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


SIMPLIFIED_CODE = """\
distance = sensor.distance_mm

if trigger.update(distance):
    response = mode.next_response(distance)
    lights[response.light_name].on()
    audio.play(response.note)
"""


CODE_STAGE_LINES = {
    "sensor": 1,
    "trigger": 3,
    "response": 4,
    "lighting": 5,
    "audio": 6,
}


LIGHT_STYLES = {
    "green": "bright_green",
    "yellow": "bright_yellow",
    "blue": "bright_blue",
}


GPIO_NAMES = {
    "green": "GPIO17",
    "yellow": "GPIO27",
    "blue": "GPIO22",
}


@dataclass(frozen=True)
class DisplayState:
    """Information shown by the terminal presentation."""

    distance_mm: int | None = None
    trigger_state: str = "ARMED"
    response_mode: str = "cycle"

    note: str | None = None
    light_name: str | None = None

    output_active: bool = False
    audio_active: bool = False

    code_stage: str = "sensor"

    special_text: str | None = None


class TerminalDisplay:
    """Render Demo 2 state as a terminal exhibit."""

    def __init__(
        self,
        console: Console | None = None,
    ) -> None:
        self.console = (
            console
            if console is not None
            else Console()
        )

    @staticmethod
    def _light_style(
        light_name: str | None,
    ) -> str:
        """Return the Rich style for a lighting channel."""

        if light_name is None:
            return "white"

        return LIGHT_STYLES.get(
            light_name,
            "white",
        )

    def _build_header(
        self,
        state: DisplayState,
        *,
        now_seconds: float,
    ) -> Panel:
        """Build the title bar."""

        title = Text()

        title.append(
            "PIANO STAIRCASE",
            style="bold bright_white",
        )

        title.append(
            "  //  ",
            style="bright_black",
        )

        title.append(
            "WSU ACM",
            style="bold bright_cyan",
        )

        title.append(
            "  //  LIVE SYSTEM",
            style="cyan",
        )

        if state.output_active:
            light_style = self._light_style(
                state.light_name
            )

            pulse = (
                int(now_seconds * 5)
                % 2
                == 0
            )

            border_style = (
                f"bold {light_style}"
                if pulse
                else light_style
            )

        elif state.special_text is not None:
            border_style = "bold bright_magenta"

        else:
            border_style = "bright_cyan"

        return Panel(
            Align.center(title),
            box=box.DOUBLE,
            border_style=border_style,
            padding=(0, 1),
        )

    def _build_code_panel(
        self,
        state: DisplayState,
    ) -> Panel:
        """Build the simplified Python execution panel."""

        highlighted_line = CODE_STAGE_LINES.get(
            state.code_stage
        )

        highlight_lines = (
            {highlighted_line}
            if highlighted_line is not None
            else set()
        )

        syntax = Syntax(
            SIMPLIFIED_CODE,
            "python",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
            highlight_lines=highlight_lines,
        )

        return Panel(
            syntax,
            title=(
                "[bold bright_cyan]"
                "SIMPLIFIED PYTHON // LOGICAL FLOW"
                "[/]"
            ),
            subtitle=(
                "[dim]"
                "SIMULATED EXECUTION • REAL CONCEPT"
                "[/]"
            ),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_signal_panel(
        self,
        state: DisplayState,
    ) -> Panel:
        """Build the hardware/software signal-flow diagram."""

        signal = Text()

        signal.append(
            " [VL53L0X]",
            style="bold bright_cyan",
        )

        signal.append(
            " ── I²C ──▶ ",
            style="cyan",
        )

        signal.append(
            "[Pi Zero 2 W]\n",
            style="bold bright_white",
        )

        signal.append(
            "                         │\n",
            style="bright_black",
        )

        signal.append(
            "                  ┌──────┴──────┐\n",
            style="bright_black",
        )

        signal.append(
            "                  │             │\n",
            style="bright_black",
        )

        signal.append(
            "                GPIO         PipeWire\n",
            style="cyan",
        )

        signal.append(
            "                  │             │\n",
            style="bright_black",
        )

        signal.append(
            "              [2N2222]       [audio]\n",
            style="bright_white",
        )

        signal.append(
            "                  │             │\n",
            style="bright_black",
        )

        signal.append(
            "                [LEDs]       [speaker]",
            style="bright_white",
        )

        return Panel(
            Align.center(signal),
            title=(
                "[bold bright_cyan]"
                "WHAT IS ACTUALLY HAPPENING?"
                "[/]"
            ),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_io_panel(
        self,
        state: DisplayState,
        *,
        now_seconds: float,
    ) -> Panel:
        """Build the live input/output panel."""

        table = Table.grid(
            expand=True,
            padding=(0, 1),
        )

        table.add_column(
            style="dim cyan",
            ratio=2,
        )

        table.add_column(
            ratio=3,
        )

        if state.distance_mm is None:
            distance = Text(
                "---- mm",
                style="dim",
            )
        else:
            distance = Text(
                f"{state.distance_mm:4d} mm",
                style="bold bright_cyan",
            )

        table.add_row(
            "VL53L0X",
            distance,
        )

        if state.trigger_state == "FIRED":
            trigger = Text(
                "● FIRED",
                style="bold bright_cyan",
            )
        else:
            trigger = Text(
                "○ ARMED",
                style="green",
            )

        table.add_row(
            "TRIGGER",
            trigger,
        )

        table.add_row(
            "MODE",
            Text(
                state.response_mode.upper(),
                style="bold white",
            ),
        )

        table.add_row(
            "",
            "",
        )

        light_style = self._light_style(
            state.light_name
        )

        if state.note is None:
            response_text = Text(
                "—",
                style="dim",
            )
        else:
            response_text = Text(
                state.note,
                style=f"bold {light_style}",
            )

            if state.light_name is not None:
                response_text.append(
                    f" / {state.light_name.upper()}",
                    style=f"bold {light_style}",
                )

        table.add_row(
            "RESPONSE",
            response_text,
        )

        if state.light_name is None:
            gpio_name = "—"
        else:
            gpio_name = GPIO_NAMES.get(
                state.light_name,
                "—",
            )

        if state.output_active:
            pulse = (
                int(now_seconds * 5)
                % 2
                == 0
            )

            gpio_style = (
                f"bold {light_style}"
                if pulse
                else light_style
            )

            gpio_text = Text(
                f"● {gpio_name} / PWM 100%",
                style=gpio_style,
            )

            transistor_text = Text(
                "● ON",
                style=gpio_style,
            )

        else:
            gpio_text = Text(
                f"○ {gpio_name}",
                style="dim",
            )

            transistor_text = Text(
                "○ OFF",
                style="dim",
            )

        table.add_row(
            "GPIO",
            gpio_text,
        )

        table.add_row(
            "2N2222",
            transistor_text,
        )

        if state.audio_active:
            audio_text = Text(
                f"▶ {state.note or 'PLAYING'}",
                style=f"bold {light_style}",
            )
        else:
            audio_text = Text(
                "■ IDLE",
                style="dim",
            )

        table.add_row(
            "AUDIO",
            audio_text,
        )

        if state.special_text is not None:
            table.add_row(
                "",
                "",
            )

            table.add_row(
                "EVENT",
                Text(
                    state.special_text,
                    style="bold bright_magenta",
                ),
            )

        border_style = (
            light_style
            if state.output_active
            else "cyan"
        )

        return Panel(
            table,
            title=(
                "[bold bright_cyan]"
                "LIVE INPUT / OUTPUT"
                "[/]"
            ),
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_promo_panel(
        self,
    ) -> Panel:
        """Build the visitor-facing promotional panel."""

        content = Group(
            Align.center(
                Text(
                    "YOU CAN BUILD THIS",
                    style="bold bright_yellow",
                )
            ),
            Text(""),
            Align.center(
                Text(
                    "Raspberry Pi Zero 2 W",
                    style="bright_white",
                )
            ),
            Align.center(
                Text(
                    "VL53L0X distance sensor",
                    style="bright_white",
                )
            ),
            Align.center(
                Text(
                    "Breadboard + 2N2222 transistors",
                    style="bright_white",
                )
            ),
            Align.center(
                Text(
                    "LEDs + Python",
                    style="bright_white",
                )
            ),
            Text(""),
            Align.center(
                Text(
                    "WSU ACM",
                    style="bold bright_cyan",
                )
            ),
            Align.center(
                Text(
                    "LEARN BY BUILDING",
                    style="bold bright_green",
                )
            ),
            Text(""),
            Align.center(
                Text(
                    "ASK US HOW IT WORKS!",
                    style="bold bright_white",
                )
            ),
        )

        return Panel(
            content,
            title=(
                "[bold bright_cyan]"
                "BUILD • BREAK • LEARN"
                "[/]"
            ),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_footer(
        self,
        state: DisplayState,
        *,
        now_seconds: float,
    ) -> Panel:
        """Build the attention-grabbing footer."""

        if state.special_text is not None:
            message = (
                f">>> {state.special_text} <<<"
            )

            style = "bold bright_magenta"

        elif state.trigger_state == "FIRED":
            if (
                state.distance_mm is not None
                and state.note is not None
                and state.light_name is not None
            ):
                message = (
                    ">>> "
                    f"{state.distance_mm} mm"
                    "  →  "
                    f"{state.note}"
                    "  →  "
                    f"{state.light_name.upper()}"
                    " <<<"
                )
            else:
                message = ">>> INTERACTION DETECTED <<<"

            style = (
                f"bold "
                f"{self._light_style(state.light_name)}"
            )

        else:
            bright = (
                int(now_seconds * 2)
                % 2
                == 0
            )

            message = (
                ">>> WAVE YOUR HAND OVER THE SENSOR <<<"
            )

            style = (
                "bold bright_cyan"
                if bright
                else "cyan"
            )

        return Panel(
            Align.center(
                Text(
                    message,
                    style=style,
                )
            ),
            box=box.DOUBLE,
            border_style=style,
            padding=(0, 1),
        )

    def render(
        self,
        state: DisplayState,
        *,
        now_seconds: float,
    ) -> Layout:
        """Render a complete terminal display frame."""

        layout = Layout()

        layout.split_column(
            Layout(
                name="header",
                size=3,
            ),
            Layout(
                name="body",
                ratio=1,
            ),
            Layout(
                name="footer",
                size=3,
            ),
        )

        layout["body"].split_row(
            Layout(
                name="left",
                ratio=3,
            ),
            Layout(
                name="right",
                ratio=2,
            ),
        )

        layout["left"].split_column(
            Layout(
                name="code",
                ratio=3,
            ),
            Layout(
                name="signal",
                ratio=2,
            ),
        )

        layout["right"].split_column(
            Layout(
                name="io",
                ratio=3,
            ),
            Layout(
                name="promo",
                ratio=2,
            ),
        )

        layout["header"].update(
            self._build_header(
                state,
                now_seconds=now_seconds,
            )
        )

        layout["code"].update(
            self._build_code_panel(
                state
            )
        )

        layout["signal"].update(
            self._build_signal_panel(
                state
            )
        )

        layout["io"].update(
            self._build_io_panel(
                state,
                now_seconds=now_seconds,
            )
        )

        layout["promo"].update(
            self._build_promo_panel()
        )

        layout["footer"].update(
            self._build_footer(
                state,
                now_seconds=now_seconds,
            )
        )

        return layout
