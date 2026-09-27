import sys
from time import monotonic
from agl.sdk import Choice, Row, Rows, Screen, Terminal, TextInput

now = {"agent": "", "line": ""}
terminal: Terminal


def report(agent: str, line: str) -> None:
    now["agent"] = agent
    now["line"] = line


async def opened(run_terminal: Terminal) -> None:
    global terminal
    terminal = run_terminal
    await terminal.show(board, since=monotonic())


async def answer(question: str, options: tuple[str, ...]) -> str:
    said = await terminal.show(asking, question=question, options=options)
    # Clears the question away, so the board redraws from the top
    print("\x1b[2J\x1b[H", end="", file=sys.__stdout__, flush=True)
    return said


def board(*, since: float) -> Screen:
    return Screen(
        Rows([
            Row(f"implement and review  {_elapsed(since)}"),
            Row(""),
            Row(f"{now['agent']}  {now['line'][:60]}"),
        ])
    )


def asking(*, question: str, options: tuple[str, ...]) -> Screen[str]:
    choices = [Choice(option, value=option) for option in options]
    return Screen(
        Rows([Row(line) for line in question.splitlines()]),
        # Typing is always offered - the answer the agent did not think of is the one worth having
        [*choices, TextInput("Answer in your own words", maps=str.strip)],
    )


def _elapsed(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
