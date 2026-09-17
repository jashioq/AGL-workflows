from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final

from agl.sdk import InputError, Run, Stop, arg, workflow

from .asking import asking
from .display import approval, board, report
from .roles import Changes, builder, designer, loaded_from, loader_check, reviewer

MAX_ROUNDS: Final = 3

# What the approval screen hands back when the person picked "say what to change" and typed
# nothing. It is neither an approval nor a change, so the screen goes back up.
NOTHING_SAID: Final = Changes("")


# Run parameters, supplied by the user
@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what the new workflow should do, in a sentence or two")

    def __post_init__(self) -> None:
        if not self.request.strip():
            raise InputError(
                "--request is empty, and it is the whole of what the designer is asked to shape: "
                "it would read a blank request, propose something arbitrary, and be paid for. Say "
                "what you want the new workflow to do"
            )


@workflow
async def workflow_builder(run: Run[Parameters]) -> None:
    # Display
    await run.terminal.show(board, since=monotonic())

    # Define agents. 'watch' displays the agent's activity string; 'ask' is how a role reaches the
    # person. Bound here and not beside the factories because the ask tool waits on this run's
    # terminal, and there is no terminal until there is a run. All three share the one tool.
    ask = asking(run.terminal)
    designing = designer(watch=partial(report, "designer"), ask=ask)
    building = builder(watch=partial(report, "builder"), ask=ask)
    reviewing = reviewer(watch=partial(report, "reviewer"), ask=ask)

    # Where the loader check runs, and the same checkout every step of this run works in. There is
    # no `run.verify` on the version this workflow requires, so the address is composed from what
    # `Run` carries; `WorkspaceProvider.open` is idempotent, so this hands back the place the walk
    # already cut rather than provisioning a second one.
    place = await run.services.workspaces.open(run.scope.label, None, run.base)

    request = run.params.request

    # Design and approval. No cap on this loop: every round costs the person a typed answer, so
    # the person is the cap, and stopping them mid-conversation would end the run on a design
    # nobody approved.
    proposing: tuple[object, ...] = (request,)
    while True:
        design = await run.step(designing, *proposing, commit="write the design down as a spec")
        while (answer := await run.terminal.show(approval, design=design)) == NOTHING_SAID:
            pass
        if answer is None:
            break
        proposing = (request, design, answer)

    # First build of what was approved
    await run.step(building, design, commit=f"build {design.name}")

    # Review and fix loop. This one is capped: the agents talk to each other and nobody is watching
    # the spend.
    for round_number in range(MAX_ROUNDS):
        report("agl", f"agl workflows {design.name}")
        verdict = await run.services.verifier.verify(loader_check(design.name), place.path)
        review = await run.step(reviewing, design, loaded_from(verdict.status, verdict.output))
        if not review.findings:
            return

        # If after MAX_ROUNDS review rounds issues are still found - stop.
        if round_number == MAX_ROUNDS - 1:
            break
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
