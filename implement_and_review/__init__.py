from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final
from agl.sdk import Run, Stop, arg, workflow
from .display import board, report
from .roles import implementer, reviewer

MAX_ROUNDS: Final = 3

# Run parameters, supplied by the user
@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what you want done, in a sentence or two")

# Define agents. 'watch' is a callback to display agent's activity string in the terminal.
implementing = implementer(watch=partial(report, "OPUS"))
reviewing = reviewer(watch=partial(report, "SOL"))

@workflow
async def implement_and_review(run: Run[Parameters]) -> None:
    # Display 
    await run.terminal.show(board, since=monotonic())

    request = run.params.request

    # First implementation run
    await run.step(implementing, request, commit="implement what the run was asked for")

    # Review and fix loop
    for _ in range(MAX_ROUNDS):
        review = await run.step(reviewing, request)
        if not review.findings:
            return
        await run.step(implementing, request, review, commit="fix what the review found")
    findings = "\n".join(review.findings)

    # If after MAX_ROUNDS review rounds issues are still found - stop.
    raise Stop(
        f"{MAX_ROUNDS} review rounds and the last one still had findings. They went back to the "
        f"implementer and nothing has reviewed that fix:\n\n{findings}"
    )
