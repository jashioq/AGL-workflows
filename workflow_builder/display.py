from time import monotonic
from agl.sdk import Choice, Row, Rows, Screen, Terminal, TextInput, Tool, ToolResult, tool
from .roles import Asked, Design

now = {"agent": "", "line": ""}


def report(agent: str, line: str) -> None:
    now["agent"] = agent
    now["line"] = line


# on_activity starts with an agent's first tool call, so each step's start is marked by hand
def began(agent: str, line: str = "") -> None:
    report(agent, line)


def board(*, since: float) -> Screen:
    return Screen(
        Rows([
            Row(f"workflow builder  {_elapsed(since)}"),
            Row(""),
            Row(f"{now['agent']}  {now['line'][:60]}"),
        ])
    )


def approval(*, design: Design) -> Screen[str | None]:
    # One row per line, or the grid rewraps the diagram
    lines = [design.name, "", *design.diagram.splitlines(), "", *design.summary.splitlines()]
    return Screen(
        Rows([Row(line) for line in lines]),
        [Choice("Approve and build it", value=None), TextInput("Ask for a change", maps=str.strip)],
    )


def question(*, asked: Asked) -> Screen[str]:
    # Typing is always offered - the answer the agent did not think of is the one worth having
    choices = [Choice(option, value=option) for option in asked.options]
    return Screen(asked.question, [*choices, TextInput("Answer in your own words", maps=str.strip)])


def asking(terminal: Terminal) -> Tool:
    async def answered(asked: Asked) -> ToolResult:
        answer = await terminal.show(question, asked=asked)
        return ToolResult(text=answer or "They typed nothing, so use your own judgement.")

    return tool(
        "ask_the_person",
        "Ask the person running this workflow a question, and wait for their answer.",
        Asked,
        answered,
    )


def _elapsed(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
