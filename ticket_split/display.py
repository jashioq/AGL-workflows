import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import monotonic
from typing import Final
from agl.sdk import Choice, Row, Rows, Screen, Terminal, TextInput

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
REVIEWING: Final = "IN REVIEW"
WAITING: Final = "WAITING"
MERGED: Final = "MERGED"

PADDING: Final = [Row("")] * 3

NAME: Final = 22
ACTIVITY: Final = 26
STATUS: Final = 40
HEADLINE: Final = 50


@dataclass(slots=True)
class Line:
    """What one ticket's row on the board is showing."""

    parent: str
    status: str = PENDING
    activity: str = ""
    started: float = 0.0
    ended: float = 0.0
    reviewers: dict[str, float] = field(default_factory=dict)


class Display:
    """The run on one screen: its name and timer, the phase it is in, and a row per ticket.

    `open` and `ask` reach the terminal and wait; every other method only records what the
    next frame will draw."""

    _terminal: Terminal

    def __init__(self) -> None:
        self._phase = ""
        self._activity = ""
        self._conflicted = ""
        self._todo = ""
        self._lines: dict[str, Line] = {}

    async def open(self, terminal: Terminal, label: str) -> None:
        """Put the board up and leave it there for the rest of the run."""
        self._terminal = terminal
        await terminal.show(self._board, label=label, since=monotonic())

    async def ask(self, question: str, options: tuple[str, ...]) -> str:
        """Put a question to the person and wait for what they pick or type.

        Clears the screen afterwards, so the next frame redraws from the top."""
        said = await self._terminal.show(self._asking, question=question, options=options)
        print("\x1b[2J\x1b[H", end="", file=sys.__stdout__, flush=True)
        return said

    def phase(self, name: str) -> None:
        """Name the phase the run has reached, and clear what the last agent was doing."""
        self._phase = name
        self._activity = ""

    def activity(self, line: str) -> None:
        """Show what the single agent of the interview or the split is doing."""
        self._activity = line

    def activity_on(self, ticket: str, line: str) -> None:
        """Show what the agent working a ticket is doing, on that ticket's row."""
        self._lines[ticket].activity = line

    def pending(self, ticket: str, parent: str = "") -> None:
        """Put a ticket on the board, indented under the ticket a review raised it from."""
        self._lines[ticket] = Line(parent)

    def working(self, ticket: str) -> None:
        """Mark a ticket as having an agent on it, and start its timer."""
        self._lines[ticket].status = RUNNING
        self._lines[ticket].started = monotonic()

    @contextmanager
    def reviewing(self, ticket: str, agent: str) -> Iterator[None]:
        """Mark a ticket as in review, naming one review agent and timing it for the block.

        Several can be open on one ticket at once, and each is shown for as long as it runs."""
        line = self._lines[ticket]
        line.status = REVIEWING
        line.reviewers[agent] = monotonic()
        try:
            yield
        finally:
            del line.reviewers[agent]

    def waiting(self, ticket: str) -> None:
        """Mark a ticket as past its own work and waiting on its tickets or on its merge."""
        self._lines[ticket].status = WAITING

    def merged(self, ticket: str) -> None:
        """Mark a ticket as landed, and stop its timer."""
        self._lines[ticket].status = MERGED
        self._lines[ticket].ended = monotonic()

    def conflicted(self, ticket: str, where: str) -> None:
        """Show a merge conflict, naming the checkout it has to be resolved in."""
        self._conflicted = ticket
        self._todo = f"git add what you fix in {where} - retried every 5s"

    def refused(self, ticket: str, where: str) -> None:
        """Show a refused merge, naming the checkout whose build has to pass."""
        self._conflicted = ticket
        self._todo = f"the build failed after merging - fix and commit in {where}"

    def cleared(self, ticket: str) -> None:
        """Take a ticket's merge banner down, leaving any other ticket's standing."""
        if self._conflicted == ticket:
            self._conflicted, self._todo = "", ""

    def _board(self, *, label: str, since: float) -> Screen:
        return Screen(
            Rows([
                *PADDING,
                Row(f"{BLUE}{label}{RESET}  {YELLOW}{_clock(since, monotonic())}{RESET}"),
                Row(""),
                *self._banner(),
                Row(f"{PURPLE}{self._phase}{RESET}  {WHITE}{self._activity[:HEADLINE]}{RESET}"),
                Row(""),
                *(self._row(ticket) for ticket in self._ordered()),
            ])
        )

    def _asking(self, *, question: str, options: tuple[str, ...]) -> Screen[str]:
        choices = [Choice(f"{WHITE}{option}{GREEN}", value=option) for option in options]
        return Screen(
            Rows([
                *PADDING,
                *self._banner(),
                *(Row(f"{WHITE}{line}{GREEN}") for line in question.splitlines()),
            ]),
            [*choices, TextInput(f"{WHITE}Answer in your own words", maps=str.strip)],
        )

    def _banner(self) -> list[Row]:
        if not self._conflicted:
            return []
        return [
            Row(f"{RED}MERGE CONFLICT: {self._conflicted}{RESET}"),
            Row(f"{FADED_RED}{self._todo}{RESET}"),
            Row(""),
        ]

    def _ordered(self) -> list[str]:
        """Every ticket in the order it is drawn, each followed by the tickets raised from it."""
        shown: list[str] = []
        for ticket, line in self._lines.items():
            if not line.parent:
                shown.append(ticket)
                shown.extend(one for one, under in self._lines.items() if under.parent == ticket)
        return shown

    def _row(self, ticket: str) -> Row:
        """One ticket's row: its name, what it is doing, its status and its timer.

        Padded here and drawn as one cell: a terminal counts colour codes toward a width."""
        line = self._lines[ticket]
        bright = line.status in (RUNNING, REVIEWING)
        named = f"    {ticket.removeprefix(line.parent + '-')}" if line.parent else ticket
        return Row(
            f"{_colour(line.parent, bright)}{_column(named, NAME)}"
            f"{WHITE if bright else FADED}{_column(line.activity, ACTIVITY)}"
            f"{_column(_status(line), STATUS)}"
            f"{YELLOW}{_elapsed(line)}{RESET}"
        )


display = Display()


def _colour(parent: str, bright: bool) -> str:
    if parent:
        return RED if bright else FADED_RED
    return WHITE if bright else FADED


def _column(text: str, width: int) -> str:
    """Text cut and padded to a fixed width, keeping a gap before the next column."""
    return f"{text[: width - 2]:<{width}}"


def _status(line: Line) -> str:
    """A ticket's status, followed in review by each agent reading it and how long it has run."""
    if not line.reviewers:
        return line.status
    now = monotonic()
    agents = ", ".join(f"{agent} {_clock(since, now)}" for agent, since in line.reviewers.items())
    return f"{line.status}: {agents}"


def _elapsed(line: Line) -> str:
    return "" if not line.started else _clock(line.started, line.ended or monotonic())


def _clock(start: float, end: float) -> str:
    seconds = int(end - start)
    return f"{seconds // 60}:{seconds % 60:02d}"
