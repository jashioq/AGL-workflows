"""Ralph: one prompt, one fresh agent, over and over, until an external command says it is done.

The technique is Geoffrey Huntley's - https://ghuntley.com/ralph - and the whole of it is that
nothing is remembered. The same prompt goes to a brand new agent each time round, so the only
way work can accumulate is on disk and in git history, and the only way an agent can learn what
its predecessors did is to read the repository. What decides that the loop is over is a build,
a test suite, a gate - something outside the agent that exits nought or does not - never the
agent announcing that it is finished.

AGL's execution model already does the first half. `run.step` fingerprints a role by *content* -
its instructions, model, restrictions, tools, inputs and the head it starts from - and dispatches
an `AgentTask` carrying that composed prompt and nothing else: no conversation, no history, no
carried state. Continuity is the git worktree, which is the same checkout for every step of a
run. So stepping one role in a loop is not an approximation of Ralph; it is Ralph, and this
workflow is mostly the other half - running the gate and feeding its failure back in.

    agl run ralph -n my-run -r "add a percentile function with tests" --gate "pytest -q"

Each iteration: the agent reads the repository and RALPH.md, does the next thing, and AGL
commits it; then the gate command runs in that same checkout. Exit nought and the run is over.
Anything else and the exit status and output go into the next iteration as a typed input, and
round again - up to `--max-iterations`, after which the run stops and says the gate still fails.
"""

from dataclasses import dataclass
from functools import partial
from time import monotonic
from typing import Final

from agl.sdk import InputError, Run, Stop, arg, workflow

from .display import began, board, report
from .roles import GateFailure, Task, failure_from, worker

# Ten, and it is a cost decision rather than a technical one. Huntley's loop has no cap: it runs
# until the gate goes green or a person stops it. A workflow spending somebody's money needs an
# end it reaches on its own, and this one is set where a run that is converging has room and a
# run that is stuck is not left to discover it fifty times. Three - what a review loop uses - is
# too few: the first iteration is usually spent reading the repository and writing the plan, so
# three is barely two attempts at the work. Raise it with --max-iterations for a larger request.
DEFAULT_MAX_ITERATIONS: Final = 10

# What the second row of the board calls each of the two things that can be working.
AGENT: Final = "OPUS"
GATE: Final = "gate"


@dataclass(frozen=True, slots=True)
class Parameters:
    """What to build, the command that decides it is built, and how many rounds to pay for."""

    request: str = arg("-r", "--request", help="what you want built, in a sentence or two")

    gate: str = arg(
        "-g", "--gate", help="the command that decides done: exit 0 ends the run, anything else "
        "goes back to the agent"
    )

    max_iterations: int = arg(
        "-m", "--max-iterations", default=DEFAULT_MAX_ITERATIONS,
        help=f"how many rounds to run before giving up (default: {DEFAULT_MAX_ITERATIONS})",
    )

    def __post_init__(self) -> None:
        if not self.request.strip():
            raise InputError(
                "--request is empty, and it is the whole of what the agent is asked to build: "
                "every iteration would read a blank request, do something arbitrary, and be paid "
                "for. Say what you want done"
            )
        if not self.gate.strip():
            raise InputError(
                "--gate is empty, and an empty command run through a shell exits 0 - so the "
                "first iteration would pass a gate that built and tested nothing, and the run "
                "would report success having verified none of it. Name the command this "
                "repository is tested with"
            )
        if self.max_iterations < 1:
            raise InputError(
                f"--max-iterations is {self.max_iterations}, and the loop is what this workflow "
                f"is: below one there is no iteration to run, so the run would stop reporting "
                f"that a gate it never ran still fails. The smallest run that does anything is 1"
            )


@workflow
async def ralph(run: Run[Parameters]) -> None:
    await run.terminal.show(board, since=monotonic())

    task = Task(request=run.params.request, gate=run.params.gate)
    iterating = worker(watch=partial(report, AGENT))

    # Where the gate runs, and the same checkout every step of this run works in. There is no
    # `run.path`, so the address is composed from what `Run` carries; `WorkspaceProvider.open` is
    # idempotent by contract, so this hands back the place the walk already cut rather than
    # provisioning a second one.
    place = await run.services.workspaces.open(run.scope.label, None, run.base)

    failure: GateFailure | None = None
    for iteration in range(1, run.params.max_iterations + 1):
        # Nothing synthetic separates these calls. Two iterations whose gate printed the same
        # thing compose the same prompt and fingerprint alike, and AGL separates them by an
        # ordinal of its own - so an iteration counter passed as an input would only corrupt
        # what a resume is able to replay.
        began(AGENT)
        given = (task,) if failure is None else (task, failure)
        await run.step(iterating, *given, commit=f"ralph iteration {iteration}")

        began(GATE, task.gate)
        verdict = await run.services.verifier.verify(task.gate, place.path)
        if verdict.passed:
            return
        failure = failure_from(verdict.status, verdict.output)

    raise Stop(_exhausted(run.params.max_iterations, task.gate, failure))


def _exhausted(rounds: int, gate: str, failure: GateFailure | None) -> str:
    ending = (
        ""
        if failure is None
        else f" The last run exited {failure.status} and said:\n\n{failure.output}"
    )
    return (
        f"ralph ran its {rounds} iterations and {gate!r} still does not pass, so the request has "
        f"not been met and nothing here says otherwise. The work each iteration did is on this "
        f"run's branch, a commit apiece, and RALPH.md in that tree is where the last one thought "
        f"it had got to - read those before deciding whether another run would converge or "
        f"whether the request needs splitting up.{ending}"
    )
