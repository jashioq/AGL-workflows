from time import monotonic
from typing import Final

from agl.sdk import Choice, Response, Row, Rows, Screen, TextInput

from .roles import Asked, Changes, Design

# The activity line is padded and cut to this because the SDK's terminal reports no width: a row
# goes into a grid that wraps what it cannot fit, so an unbounded line turns three rows into six
# and the board jumps about. Padded as well as cut so what sits beside it stays still.
_ACTIVITY: Final = 58

# Long enough for the longest label this workflow binds below, so the activity column does not
# shift when one role takes over from another.
_WHO: Final = 8

APPROVE: Final = "Approve - write the spec and build it"

CHANGE: Final = "Say what you want changed"

FREE_TEXT: Final = "Answer in your own words"

now = {"agent": "", "line": ""}


def report(agent: str, line: str) -> None:
    now["agent"] = agent
    now["line"] = line


def board(*, since: float) -> Screen:
    return Screen(
        Rows([
            Row(f"workflow builder  {_elapsed(since)}"),
            Row(""),
            Row(f"{now['agent']:<{_WHO}.{_WHO}}  {now['line']:<{_ACTIVITY}.{_ACTIVITY}}"),
        ])
    )


def approval(*, design: Design) -> Screen[Changes | None]:
    return Screen(
        Rows([Row(line) for line in _proposed(design)]),
        [Choice(APPROVE, value=None), TextInput(CHANGE, maps=Changes)],
    )


def question(*, asked: Asked) -> Screen[str]:
    responses: list[Response[str]] = [Choice(option, value=option) for option in asked.options]
    # Offered last and always: an option the model did not think of is the answer worth having,
    # and a question whose every answer was written by the agent is not really being asked.
    responses.append(TextInput(FREE_TEXT, maps=str))
    return Screen(asked.question, responses)


# One row per line, because a grid cell holding newlines is drawn as one cell and rewrapped: the
# diagram is only a diagram for as long as its lines stay where the designer put them.
def _proposed(design: Design) -> tuple[str, ...]:
    return (design.name, "", *design.diagram.splitlines(), "", *design.summary.splitlines())


def _elapsed(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
