from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final
from agl.sdk import Run, Stop, arg, workflow
from .display import board, report
from .roles import implementer, reviewer

_ROUNDS: Final = 3

@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what you want done, in a sentence or two")


@workflow
async def implement_and_review(run: Run[Parameters]) -> None:
    await run.terminal.show(board, since=monotonic())
    implementing = implementer(watch=partial(report, "OPUS"))
    reviewing = reviewer(watch=partial(report, "SOL"))

    request = run.params.request
    await run.step(implementing, request, commit="implement what the run was asked for")
    for _ in range(_ROUNDS):
        review = await run.step(reviewing, request)
        if not review.findings:
            return
        await run.step(implementing, request, review, commit="fix what the review found")
    findings = "\n".join(review.findings)
    raise Stop(
        f"{_ROUNDS} review rounds and the last one still had findings. They went back to the "
        f"implementer and nothing has reviewed that fix:\n\n{findings}"
    )
