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

from piano_staircase_demo.pipes import PipeSnapshot


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

    pipe_mode_active: bool = False
    pipe_mode_seconds_remaining: float | None = None
    pipe_unlock_moves: int = 0
    pipe_unlock_move_target: int = 5
    pipe_unlock_reversals: int = 0
    pipe_unlock_reversal_target: int = 3
    pipe_snapshots: tuple[PipeSnapshot, ...] = ()


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

    @staticmethod
    def _midi_note_name(midi_note: int) -> str:
        """Return a compact note label such as F#4 for display use."""

        names = (
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B",
        )
        octave = midi_note // 12 - 1
        return f"{names[midi_note % 12]}{octave}"

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

        if state.pipe_mode_active:
            title.append(
                "  //  PIPE PHYSICS MODE",
                style="bold bright_magenta",
            )
        else:
            title.append(
                "  //  LIVE SYSTEM",
                style="cyan",
            )

        if state.pipe_mode_active:
            border_style = "bold bright_magenta"

        elif state.output_active:
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

        if state.trigger_state == "PIPE":
            trigger = Text(
                "● PIPE PHYSICS",
                style="bold bright_magenta",
            )
        elif state.trigger_state == "FIRED":
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

    def _build_pipe_equations_panel(
        self,
    ) -> Panel:
        """Explain the simplified physics model used by procedural pipes."""

        content = Group(
            Text("ROCKING / IMPACT TIMING", style="bold bright_magenta"),
            Text("Δt ≈ 4 √(Lθ / 3g)", style="bold bright_white"),
            Text("θₙ = θ₀ · r²ⁿ", style="bright_white"),
            Text("  L = pipe length   θ = rocking angle", style="dim"),
            Text("  r = restitution   g = gravity", style="dim"),
            Text(""),
            Text("STRUCTURAL RESONANCE", style="bold bright_cyan"),
            Text("f ∝ (1/L²) √(EI / μ)", style="bold bright_white"),
            Text("I = π(D⁴ − d⁴) / 64", style="bright_white"),
            Text("μ = ρA", style="bright_white"),
            Text("A = π(D² − d²) / 4", style="bright_white"),
            Text(""),
            Text(
                "Simplified educational rigid-body / beam model",
                style="dim italic",
            ),
        )

        return Panel(
            content,
            title="[bold bright_magenta]SIMPLIFIED PIPE PHYSICS[/]",
            border_style="bright_magenta",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_pipe_model_panel(
        self,
        state: DisplayState,
    ) -> Panel:
        """Show live physical parameters for the newest active pipe."""

        if not state.pipe_snapshots:
            content = Align.center(
                Text(
                    "No pipe is falling right now.\n\n"
                    "Reverse direction to launch another.",
                    style="bold bright_white",
                    justify="center",
                ),
                vertical="middle",
            )
        else:
            pipe = state.pipe_snapshots[-1]
            inner_diameter_mm = max(
                0.0,
                pipe.outer_diameter_mm - 2.0 * pipe.wall_thickness_mm,
            )

            table = Table.grid(expand=True, padding=(0, 1))
            table.add_column(style="dim bright_magenta", ratio=2)
            table.add_column(ratio=3)

            table.add_row(
                "PIPE",
                Text(f"#{pipe.pipe_id} / MIDI CH {pipe.channel}",
                     style="bold white"),
            )
            table.add_row(
                "MATERIAL",
                Text(pipe.material.upper(), style="bold bright_white"),
            )
            table.add_row("LENGTH L", f"{pipe.length_m:.3f} m")
            table.add_row("OUTER D", f"{pipe.outer_diameter_mm:.1f} mm")
            table.add_row("INNER d", f"{inner_diameter_mm:.1f} mm")
            table.add_row("WALL", f"{pipe.wall_thickness_mm:.2f} mm")
            table.add_row("RESTITUTION r", f"{pipe.restitution:.3f}")
            table.add_row(
                "IMPACTS",
                f"{pipe.impact_number}/{pipe.impact_count}",
            )

            if pipe.next_impact_seconds is None:
                next_impact = "FINAL RING"
            elif pipe.next_impact_seconds <= 0.005:
                next_impact = "NOW"
            else:
                next_impact = f"{pipe.next_impact_seconds:.3f} s"

            table.add_row("NEXT IMPACT", next_impact)
            table.add_row(
                "RESONANCES",
                (
                    f"{self._midi_note_name(pipe.low_resonance)} + "
                    f"{self._midi_note_name(pipe.high_resonance)} "
                    f"(MIDI {pipe.low_resonance}/{pipe.high_resonance})"
                ),
            )
            table.add_row("SEED", str(pipe.seed))
            content = table

        return Panel(
            content,
            title="[bold bright_cyan]LIVE PIPE MODEL[/]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_pipe_list_panel(
        self,
        state: DisplayState,
    ) -> Panel:
        """Show every concurrently active procedural pipe."""

        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column(style="dim bright_magenta")
        table.add_column()
        table.add_column(justify="right")

        table.add_row("PIPE", "MATERIAL", "IMPACT")

        if not state.pipe_snapshots:
            table.add_row("—", "waiting for reversal", "—")
        else:
            for pipe in state.pipe_snapshots:
                table.add_row(
                    f"#{pipe.pipe_id}",
                    pipe.material,
                    f"{pipe.impact_number}/{pipe.impact_count}",
                )

        table.add_row("", "", "")
        table.add_row(
            "ACTIVE",
            f"{len(state.pipe_snapshots)} / 6 simultaneous channels",
            "",
        )

        return Panel(
            table,
            title="[bold bright_magenta]FALLING PIPES[/]",
            border_style="bright_magenta",
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _build_pipe_control_panel(
        self,
        state: DisplayState,
    ) -> Panel:
        """Tell a visitor how continued motion controls Pipe Physics Mode."""

        remaining = state.pipe_mode_seconds_remaining
        countdown = (
            f"{remaining:.1f} s"
            if remaining is not None
            else "—"
        )

        content = Group(
            Align.center(
                Text("YOU UNLOCKED PHYSICS MODE", style="bold bright_magenta")
            ),
            Text(""),
            Align.center(
                Text("KEEP MOVING YOUR HAND", style="bold bright_white")
            ),
            Align.center(
                Text("Each direction reversal can drop another pipe.", style="white")
            ),
            Align.center(
                Text("LEDs: TOP → MIDDLE → BOTTOM → BOUNCE", style="bright_cyan")
            ),
            Text(""),
            Align.center(
                Text("MODE ENDS WITHOUT MOVEMENT IN", style="dim")
            ),
            Align.center(
                Text(countdown, style="bold bright_yellow")
            ),
            Text(""),
            Align.center(
                Text(
                    "Every pipe randomizes size, material, timing, and pitch.",
                    style="bright_cyan",
                )
            ),
        )

        return Panel(
            Align.center(content, vertical="middle"),
            title="[bold bright_yellow]KEEP PLAYING[/]",
            border_style="bright_yellow",
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

        if state.pipe_mode_active:
            remaining = state.pipe_mode_seconds_remaining
            countdown = (
                f"{remaining:.1f}s"
                if remaining is not None
                else "ACTIVE"
            )
            message = (
                ">>> PIPE PHYSICS MODE  //  KEEP MOVING  //  "
                f"{countdown} <<<"
            )
            style = "bold bright_magenta"

        elif state.pipe_unlock_moves > 0:
            message = (
                ">>> RAPID MOTION  //  "
                f"{state.pipe_unlock_moves}/{state.pipe_unlock_move_target} MOVES  •  "
                f"{state.pipe_unlock_reversals}/{state.pipe_unlock_reversal_target} REVERSALS  "
                "//  KEEP GOING <<<"
            )
            style = "bold bright_magenta"

        elif state.special_text is not None:
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

        if state.pipe_mode_active:
            layout["code"].update(
                self._build_pipe_equations_panel()
            )
            layout["signal"].update(
                self._build_pipe_model_panel(state)
            )
            layout["io"].update(
                self._build_pipe_list_panel(state)
            )
            layout["promo"].update(
                self._build_pipe_control_panel(state)
            )
        else:
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
