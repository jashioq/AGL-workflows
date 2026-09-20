from time import monotonic
from agl.sdk import Row, Rows, Screen

now = {"agent": "", "line": ""}


def report(agent: str, line: str) -> None:
    now["agent"] = agent
    now["line"] = line


def board(*, since: float) -> Screen:
    return Screen(
        Rows([
            Row(f"implement and review  {_elapsed(since)}"),
            Row(""),
            Row(f"{now['agent']}  {now['line'][:60]}"),
        ])
    )


def _elapsed(since: float) -> str:
    seconds = int(monotonic() - since)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
