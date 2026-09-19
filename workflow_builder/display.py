import sys
from time import monotonic
from typing import Final
from agl.sdk import Choice, Role, Row, Rows, Screen, Terminal, TextInput

BLUE: Final = "\x1b[1;38;2;70;160;255m"
YELLOW: Final = "\x1b[1;38;2;255;220;0m"
PURPLE: Final = "\x1b[1;38;2;200;90;255m"
GREEN: Final = "\x1b[1;38;2;0;255;120m"
WHITE: Final = "\x1b[0;38;2;255;255;255m"
RESET: Final = "\x1b[0m"

# Keeps the run apart from the warnings agl prints before it starts
PADDING: Final = [Row("")] * 3

now = {"agent": "", "line": ""}
terminal: Terminal


def report(agent: str, line: str) -> None:
    now["agent"] = agent
    now["line"] = line


# on_activity starts with an agent's first tool call, so each step's start is marked by hand
def began[P](role: Role[P]) -> None:
    report(role.name, "")


async def opened(run_terminal: Terminal) -> None:
    global terminal
    terminal = run_terminal
    await terminal.show(board, since=monotonic())


async def answer(question: str, options: tuple[str, ...]) -> str:
    said = await terminal.show(asking, question=question, options=options)
    # The echoed answer throws off where the terminal redraws from, so old questions stay behind
    print("\x1b[2J\x1b[H", end="", file=sys.__stdout__, flush=True)
    return said


def board(*, since: float) -> Screen:
    return Screen(
        Rows([
            *PADDING,
            Row(f"{BLUE}workflow builder{RESET}  {YELLOW}{_elapsed(since)}{RESET}"),
            Row(""),
            Row(f"{PURPLE}{now['agent']}{RESET}  {WHITE}{now['line'][:60]}{RESET}"),
        ])
    )


def asking(*, question: str, options: tuple[str, ...]) -> Screen[str]:
    # agl numbers the answers itself, so each line ends by turning the number after it green
    choices = [Choice(f"{WHITE}{option}{GREEN}", value=option) for option in options]
    # One row per line, or the grid rewraps a design's diagram
    return Screen(
        Rows([*PADDING, *(Row(f"{WHITE}{line}{GREEN}") for line in question.splitlines())]),
        # Typing is always offered - the answer the agent did not think of is the one worth having
        [*choices, TextInput(f"{WHITE}Answer in your own words", maps=str.strip)],
    )


def _elapsed(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
