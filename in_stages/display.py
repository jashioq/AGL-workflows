import shutil
from dataclasses import dataclass
from time import monotonic
from typing import Final
from agl.sdk import Row, Rows, Screen, Terminal

# The chat workflow's orange for Claude. A colour is spelled once, bright, and a row that is not
# being worked on puts DIM in front of it
ORANGE: Final = "\x1b[38;5;209m"
YELLOW: Final = "\x1b[93m"
GREEN: Final = "\x1b[92m"
PURPLE: Final = "\x1b[95m"
WHITE: Final = "\x1b[97m"
DIM: Final = "\x1b[2m"
RESET: Final = "\x1b[0m"

AGENT: Final = "Sonnet"


@dataclass(slots=True)
class Line:
    name: str
    started: float = 0.0
    ended: float = 0.0


lines: list[Line] = []


async def opened(terminal: Terminal, label: str, stages: int) -> None:
    await terminal.show(board, label=label, stages=stages, since=monotonic())


def planned(names: list[str]) -> None:
    lines[:] = [Line(name) for name in names]


def started(stage: int) -> None:
    lines[stage].started = monotonic()


def finished(stage: int) -> None:
    lines[stage].ended = monotonic()


def board(*, label: str, stages: int, since: float) -> Screen:
    width = shutil.get_terminal_size().columns
    done = sum(1 for line in lines if line.ended)
    # Until the split comes back there are no stages to list, so the split has the one row
    shown = lines or [Line(f"Split into {stages} stages", started=since)]
    return Screen(
        Rows([
            Row(
                f"{YELLOW}{label}{RESET} - {done} of {len(lines) or stages} done - "
                f"{PURPLE}{_clock(since, monotonic())}{RESET}"
            ),
            Row(""),
            *(_row(line, width) for line in shown),
        ])
    )


def _row(line: Line, width: int) -> Row:
    if line.ended:
        tone, colour, status = DIM, GREEN, "DONE"
    elif line.started:
        tone, colour, status = "", YELLOW, "IN PROGRESS"
    else:
        tone, colour, status = DIM, YELLOW, "PENDING"
    timer = f" {_clock(line.started, line.ended or monotonic())}" if line.started else ""
    head = f"{tone}{ORANGE}{AGENT}: {WHITE}"
    tail = f" - {colour}{status}{PURPLE}{timer}{RESET}"
    # The escapes are counted as columns of the row carrying them, so they come off what the name
    # may hold - a row counted wider than the terminal is folded onto a second line
    room = max(width - len(head) - len(tail), 1)
    return Row(f"{head}{line.name[:room]}{tail}")


def _clock(start: float, end: float) -> str:
    seconds = int(end - start)
    return f"{seconds // 60}:{seconds % 60:02d}"
