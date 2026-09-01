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
transition = zones.update(distance)

if transition:
    response = zone_responses[transition.current_zone]
    lights.set(response.light_names)
    synth.play(response.notes)
"""


CODE_STAGE_LINES = {
    "sensor": 1,
    "trigger": 2,
    "response": 5,
    "lighting": 6,
    "audio": 7,
}


LIGHT_STYLES = {
    "green": "bright_green",
    "green+yellow": "bright_yellow",
    "yellow": "bright_yellow",
    "yellow+blue": "bright_blue",
    "blue": "bright_blue",
}


# Physical assignments for the final Demo 2 wiring.
GPIO_NAMES = {
    "green": "GPIO22",
    "yellow": "GPIO27",
    "blue": "GPIO17",
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
    def _light_names(
        light_name: str | None,
    ) -> tuple[str, ...]:
        """Split one display light label into individual channel names."""

        if light_name is None:
            return ()

        return tuple(
            name.strip().lower()
            for name in light_name.split("+")
            if name.strip()
        )

    @classmethod
    def _format_light_name(
        cls,
        light_name: str | None,
    ) -> str:
        """Return a visitor-facing label such as GREEN + YELLOW."""

        names = cls._light_names(light_name)
        return " + ".join(name.upper() for name in names)

    @staticmethod
    def _light_style(
        light_name: str | None,
    ) -> str:
        """Return the Rich style for one or two active lighting channels."""

        if light_name is None:
            return "white"

        return LIGHT_STYLES.get(
            light_name.lower(),
            "white",
        )

    @classmethod
    def _gpio_label(
        cls,
        light_name: str | None,
    ) -> str:
        """Return the GPIO label for one or two active staircase rails."""

        labels = [
            GPIO_NAMES[name]
            for name in cls._light_names(light_name)
            if name in GPIO_NAMES
        ]

        return " + ".join(labels) if labels else "—"

    @classmethod
    def _active_channel_count(
        cls,
        light_name: str | None,
    ) -> int:
        """Return the number of named lighting channels in a display state."""

        return len(cls._light_names(light_name))

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
        """Build the simplified hardware/software signal-flow diagram."""

        signal = Text()

        signal.append(
            "[VL53L0X]",
            style="bold bright_cyan",
        )

        signal.append(
            " ── I²C ──▶ ",
            style="cyan",
        )

        signal.append(
            "[Pi Zero 2 W]",
            style="bold bright_white",
        )

        signal.append("\n\n")

        signal.append(
            "GPIO",
            style="bold bright_cyan",
        )

        signal.append(
            " ──▶ ",
            style="cyan",
        )

        signal.append(
            "[2N2222]",
            style="bold bright_white",
        )

        signal.append(
            " ──▶ ",
            style="cyan",
        )

        signal.append(
            "[LEDs]",
            style="bold bright_white",
        )

        signal.append("\n")

        signal.append(
            "Audio",
            style="bold bright_cyan",
        )

        signal.append(
            " ───────────────▶ ",
            style="cyan",
        )

        signal.append(
            "[speaker]",
            style="bold bright_white",
        )

        return Panel(
            Align.center(
                signal,
                vertical="middle",
            ),
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
        elif state.trigger_state == "HELD":
            trigger = Text(
                "● TRACKING",
                style="bold bright_green",
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

            formatted_lights = self._format_light_name(
                state.light_name
            )

            if formatted_lights:
                response_text.append(
                    f" / {formatted_lights}",
                    style=f"bold {light_style}",
                )

        table.add_row(
            "RESPONSE",
            response_text,
        )

        gpio_name = self._gpio_label(
            state.light_name
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

            channel_count = self._active_channel_count(
                state.light_name
            )

            transistor_label = (
                "● ON"
                if channel_count <= 1
                else f"● {channel_count} CHANNELS ON"
            )

            transistor_text = Text(
                transistor_label,
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
                    "Raspberry Pi • Sensor • Breadboard",
                    style="bright_white",
                )
            ),

            Align.center(
                Text(
                    "Transistors • LEDs • Python",
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
            Align.center(
                content,
                vertical="middle",
            ),
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

        elif state.trigger_state in ("FIRED", "HELD"):
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
                    f"{self._format_light_name(state.light_name)}"
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
                ratio=1,
            ),
            Layout(
                name="signal",
                ratio=1,
            ),
        )

        layout["right"].split_column(
            Layout(
                name="io",
                ratio=1,
            ),
            Layout(
                name="promo",
                ratio=1,
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
