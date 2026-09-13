from dataclasses import dataclass, field
from time import monotonic
from typing import Final

from agl.sdk import Row, Rows, Screen

# The activity line is padded and cut to this, because `agl.sdk.Terminal` reports no width: the
# rows go into a grid that wraps what it cannot fit, so an unbounded line turns two rows into
# five and the board jumps about. Padded as well as cut so the timer beside it stays still.
_ACTIVITY: Final = 54

# Long enough for the longest label this workflow uses, so the activity column does not shift
# when the gate takes over from the agent.
_WHO: Final = 5


@dataclass(slots=True)
class _Now:
    """Who is working, what they last said, and when they started. One run, one of these."""

    who: str = ""

    line: str = ""

    since: float = field(default_factory=monotonic)


_now: Final = _Now()


def began(who: str, line: str = "") -> None:
    """Say that something else is working now, and restart its own timer.

    Called by the workflow and never by the engine: `on_activity` fires only when an agent says
    something, so the moment a step starts is the workflow's to notice.

    :param who: the label shown in the left column - an agent, or the gate
    :param line: what to show until the first activity arrives; blank for an agent
    """
    _now.who = who
    _now.line = line
    _now.since = monotonic()


def report(who: str, line: str) -> None:
    """The `on_activity` reporter. Two assignments, and deliberately nothing else.

    This runs as author code inside the engine, between the agent being paid for and its entry
    being written, and what it raises ends the run there. So nothing here formats, measures,
    slices or allocates - `board` does all of that, on the terminal's own frame.

    :param who: bound by the workflow with `partial`, so the callback takes one argument
    :param line: whatever the agent last said it was doing
    """
    _now.who = who
    _now.line = line


def board(*, since: float) -> Screen:
    """Two lines: the run and its clock, then whoever is working, what they are doing, and theirs.

    :param since: when the run started, handed to `terminal.show` once and back here each frame
    :return: a passive screen - no responses, so it goes in the slot and nobody is waited for
    """
    return Screen(
        Rows([
            Row(f"ralph  {_clock(since)}"),
            Row(
                f"{_now.who:<{_WHO}.{_WHO}}  "
                f"{_now.line:<{_ACTIVITY}.{_ACTIVITY}}  "
                f"{_clock(_now.since)}"
            ),
        ])
    )


def _clock(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
