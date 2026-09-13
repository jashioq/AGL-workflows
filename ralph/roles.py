from dataclasses import dataclass
from typing import Final

from agl.sdk import ActivityReporter, Capability, Claude, Restriction, Role, prompt_file, role

# How much of a failing gate's output is carried into the next iteration. The whole of it would go
# into the prompt, into the step's fingerprint and into the ledger, and a test suite that fails
# loudly prints megabytes - so the tail is kept, which is where a test runner puts its summary,
# and the agent is told when it was cut so it can run the gate again for the rest.
OUTPUT_KEPT: Final = 8000


@dataclass(frozen=True, slots=True)
class Task:
    """What every iteration is handed: the request, and the command that decides it is done.

    One type holding both, because a step's inputs are matched to `accepts=` by `isinstance` and
    recorded one per declared type - two bare `str` inputs would be two values for one slot.
    """

    request: str

    gate: str


@dataclass(frozen=True, slots=True)
class GateFailure:
    """The last gate run, when it failed: what it exited with, and what it printed."""

    status: int

    output: str

    truncated: bool


def failure_from(status: int, output: str) -> GateFailure:
    """Build the input the next iteration reads out of a verdict the gate produced.

    :param status: the command's exit status, which is nought for exactly the runs that passed
    :param output: stdout and stderr as the gate printed them, interleaved
    :return: the failure, its output cut to the tail `OUTPUT_KEPT` admits and marked if it was
    """
    kept = output[-OUTPUT_KEPT:]
    return GateFailure(status=status, output=kept, truncated=len(kept) != len(output))


@role(model=Claude.OPUS, accepts=(Task, GateFailure))
def worker(watch: ActivityReporter) -> Role[None]:
    """The one role. Every iteration builds this again, and every step gets a fresh agent.

    `NO_VCS_WRITES` because this run's branch is the only copy of what earlier iterations did:
    an agent free to reset, amend or rebase can throw away the memory the loop is built on.
    Reads are untouched, so `git log` and `git show` - which are the memory - stay available.
    """
    return Role(
        name="iterate",
        instructions=prompt_file("prompts/iterate.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        requires={Capability.FILE_EDIT, Capability.SHELL},
        on_activity=watch,
    )
