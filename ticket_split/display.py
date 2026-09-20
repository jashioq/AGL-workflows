import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final
from agl.sdk import Choice, Row, Rows, Screen, Terminal, TextInput

# Short codes, because the adapter sizes a row by its bytes and truecolor spends 19 on each span
BLUE: Final = "\x1b[94m"
PURPLE: Final = "\x1b[95m"
GREEN: Final = "\x1b[92m"
WHITE: Final = "\x1b[97m"
RED: Final = "\x1b[91m"
YELLOW: Final = "\x1b[2;33m"
FADED: Final = "\x1b[2;37m"
FADED_RED: Final = "\x1b[2;31m"
RESET: Final = "\x1b[0m"

PENDING: Final = "PENDING"
RUNNING: Final = "IN PROGRESS"
WAITING: Final = "WAITING"
MERGED: Final = "MERGED"

# Keeps the run apart from the warnings agl prints before it starts
PADDING: Final = [Row("")] * 3

NAME: Final = 22
ACTIVITY: Final = 26
STATUS: Final = 13
HEADLINE: Final = 50

phase = {"name": "", "line": ""}
conflict = {"ticket": "", "todo": ""}
terminal: Terminal


@dataclass(slots=True)
class Line:
    parent: str
    status: str = PENDING
    activity: str = ""
    started: float = 0.0
    ended: float = 0.0


lines: dict[str, Line] = {}


async def opened(run_terminal: Terminal, label: str) -> None:
    global terminal
    terminal = run_terminal
    await terminal.show(board, label=label, since=monotonic())


def entered(name: str) -> None:
    phase["name"] = name
    phase["line"] = ""


def report(line: str) -> None:
    phase["line"] = line


def listed(name: str, parent: str = "") -> None:
    lines[name] = Line(parent)


def at(name: str, status: str) -> None:
    line = lines[name]
    line.status = status
    if status == RUNNING:
        line.started = monotonic()
    if status == MERGED:
        line.ended = monotonic()


def watching(name: str) -> Callable[[str], None]:
    return partial(noted, name)


def noted(name: str, line: str) -> None:
    lines[name].activity = line


def conflicting(ticket: str, where: str) -> None:
    conflict["ticket"] = ticket
    conflict["todo"] = f"git add what you fix in {where} - retried every 5s"


def gate_refused(ticket: str, where: str) -> None:
    conflict["ticket"] = ticket
    conflict["todo"] = f"the build failed after merging - fix and commit in {where}"


# Two targets can each hold a landing, so a banner is cleared only by the ticket that raised it
def resolved(ticket: str) -> None:
    if conflict["ticket"] == ticket:
        conflict.update({"ticket": "", "todo": ""})


async def answer(question: str, options: tuple[str, ...]) -> str:
    said = await terminal.show(asking, question=question, options=options)
    # The echoed answer throws off where the terminal redraws from, so old questions stay behind
    print("\x1b[2J\x1b[H", end="", file=sys.__stdout__, flush=True)
    return said


def board(*, label: str, since: float) -> Screen:
    return Screen(
        Rows([
            *PADDING,
            Row(f"{BLUE}{label}{RESET}  {YELLOW}{_clock(since, monotonic())}{RESET}"),
            Row(""),
            *_banner(),
            Row(f"{PURPLE}{phase['name']}{RESET}  {WHITE}{phase['line'][:HEADLINE]}{RESET}"),
            Row(""),
            *(_line(name) for name in _ordered()),
        ])
    )


def asking(*, question: str, options: tuple[str, ...]) -> Screen[str]:
    # agl numbers the answers itself, so each line ends by turning the number after it green
    choices = [Choice(f"{WHITE}{option}{GREEN}", value=option) for option in options]
    # One row per line, or the grid rewraps a round of questions
    return Screen(
        Rows([
            *PADDING,
            *_banner(),
            *(Row(f"{WHITE}{line}{GREEN}") for line in question.splitlines()),
        ]),
        # Typing is always offered - the answer the agent did not think of is the one worth having
        [*choices, TextInput(f"{WHITE}Answer in your own words", maps=str.strip)],
    )


def _banner() -> list[Row]:
    if not conflict["ticket"]:
        return []
    return [
        Row(f"{RED}MERGE CONFLICT: {conflict['ticket']}{RESET}"),
        Row(f"{FADED_RED}{conflict['todo']}{RESET}"),
        Row(""),
    ]


def _ordered() -> list[str]:
    shown: list[str] = []
    for name, line in lines.items():
        if not line.parent:
            shown.append(name)
            shown.extend(bug for bug, under in lines.items() if under.parent == name)
    return shown


def _line(name: str) -> Row:
    line = lines[name]
    bright = line.status == RUNNING
    # A bug already sits under its parent here, so its name is drawn without the parent it carries
    named = f"    {name.removeprefix(line.parent + '-')}" if line.parent else name
    # One escape a span and one to close: every byte of them counts toward the row's width
    return Row(
        f"{_colour(line.parent, bright)}{_column(named, NAME)}"
        f"{WHITE if bright else FADED}{_column(line.activity, ACTIVITY)}"
        f"{_column(line.status, STATUS)}"
        f"{YELLOW}{_elapsed(line)}{RESET}"
    )


def _colour(parent: str, bright: bool) -> str:
    if parent:
        return RED if bright else FADED_RED
    return WHITE if bright else FADED


def _column(text: str, width: int) -> str:
    # Cut two short of the column so a cell filling it still has a gap before the next one
    return f"{text[: width - 2]:<{width}}"


def _elapsed(line: Line) -> str:
    return "" if not line.started else _clock(line.started, line.ended or monotonic())


def _clock(start: float, end: float) -> str:
    seconds = int(end - start)
    return f"{seconds // 60}:{seconds % 60:02d}"
