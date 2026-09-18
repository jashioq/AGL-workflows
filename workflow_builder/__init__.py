from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final
from agl.sdk import Run, Stop, arg, workflow
from .display import approval, asking, began, board, report
from .roles import Changes, builder, designer, loader_check, reviewer

MAX_ROUNDS: Final = 3

@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="the workflow you want built, in a sentence or two")

@workflow
async def workflow_builder(run: Run[Parameters]) -> None:
    await run.terminal.show(board, since=monotonic())

    # Bound in here rather than at module level, because the ask tool needs this run's terminal
    ask = asking(run.terminal)
    designing = designer(watch=partial(report, "designer"), ask=ask)
    building = builder(watch=partial(report, "builder"), ask=ask)
    reviewing = reviewer(watch=partial(report, "reviewer"), ask=ask)

    request = run.params.request

    # No cap on design rounds - each one waits on the person, so they decide when it ends
    began("designer")
    design = await run.step(designing, request, commit="write the design down as a spec")
    while (answer := await run.terminal.show(approval, design=design)) is not None:
        # A blank answer is neither an approval nor a change, so the screen just comes back
        if answer:
            began("designer")
            changes = Changes(answer)
            design = await run.step(designing, request, design, changes, commit="revise the spec")

    began("builder")
    await run.step(building, design, commit=f"build {design.name}")

    # Review and fix loop, capped because nobody is watching the agents answer each other
    for round_number in range(MAX_ROUNDS):
        began("agl", f"agl workflows {design.name}")
        # Load it in this run's own checkout, so the reviewer starts from a verdict, not a guess
        loaded = await run.verify(loader_check(design.name))
        began("reviewer")
        review = await run.step(reviewing, design, loaded)
        if not review.findings:
            return

        # If after MAX_ROUNDS review rounds issues are still found - stop.
        if round_number == MAX_ROUNDS - 1:
            break
        began("builder")
        await run.step(
            building,
            design,
            review,
            commit=f"fix what review round {round_number + 1} found",
        )
    findings = "\n".join(review.findings)

    raise Stop(
        f"{MAX_ROUNDS} review rounds and the last one still had findings:\n\n{findings}"
    )
