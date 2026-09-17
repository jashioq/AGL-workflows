import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from agl.sdk import (
    ActivityReporter,
    Claude,
    ReportingTool,
    Restriction,
    Role,
    Tool,
    describe,
    prompt_file,
    reporting_tool,
    role,
)

# How much of the loader check's output the reviewer is handed. A refusal out of `agl workflows` is
# a paragraph and fits whole; a traceback out of the new workflow's own import is not, and the tail
# is where the line that raised is.
OUTPUT_KEPT: Final = 4000

# The `agl` beside the interpreter running this workflow, rather than whatever `agl` a PATH happens
# to hold. The loader check asks "does the AGL running this load what it just wrote", and that is a
# question about this installation; a run started as `.venv/bin/agl` puts nothing on PATH.
_AGL: Final = Path(sys.executable).parent / "agl"


@dataclass(frozen=True, slots=True)
class Design:
    """The shape the designer proposes, and, once approved, the builder's brief and the yardstick."""

    name: str = describe(
        "The new workflow's name: its directory, its module and the name `agl run` takes. Lower "
        "case, words joined by underscores, and a name no workflow in this repository already has."
    )

    diagram: str = describe(
        "A diagram of the shape in plain characters, at most 70 columns wide. Roles with their "
        "models, the order of the steps, where a loop is and what caps it, what each role reports."
    )

    summary: str = describe(
        "What the workflow does and the one or two decisions behind the shape, in at most four "
        "lines of at most 70 characters each. The person reads this beside the diagram."
    )


@dataclass(frozen=True, slots=True)
class Asked:
    """One question a role wants answered, as the model filled it in."""

    question: str = describe("What you are asking, in full, in your own words.")

    options: tuple[str, ...] = describe(
        "The answers you are suggesting, if any. Each one is the exact text that comes back as the "
        "answer, so write them as answers rather than as labels.",
        default=(),
    )


@dataclass(frozen=True, slots=True)
class Changes:
    """What the person typed at the approval screen, which is the next design round's instruction."""

    asked: str

    def __post_init__(self) -> None:
        # Stripped here so the workflow tests a blank line with one comparison, and so the same
        # words typed with different whitespace fingerprint alike and replay one another.
        object.__setattr__(self, "asked", self.asked.strip())


@dataclass(frozen=True, slots=True)
class Loaded:
    """What the loader check said: a review that only reads source passes a workflow that refuses."""

    passed: bool

    status: int

    output: str

    truncated: bool


@dataclass(frozen=True, slots=True)
class Review:
    findings: list[str] = describe(
        "each finding as one markdown item saying where and what is wrong; empty when there are none"
    )


def loader_check(name: str) -> str:
    """The command that decides the new workflow loads, run in a throwaway AGL home holding only it.

    Two commands and not one. `agl workflows` reads what each workspace directory declares and
    imports nothing, so it lists a workflow whose first line raises; `agl workflows <name>` is the
    one that imports the module, calls its role factories and settles `accepts=` against the prompt.

    :param name: the new workflow's directory in this checkout, which is also its declared name
    :return: one shell command; the temporary home is taken away whichever way the check went
    """
    return (
        f'home=$(mktemp -d) && mkdir -p "$home/workspace/workflows" '
        f'&& cp -R {name} "$home/workspace/workflows/" '
        f'&& AGL_HOME="$home" {_AGL} workflows && AGL_HOME="$home" {_AGL} workflows {name}; '
        f'status=$?; rm -rf "$home"; exit $status'
    )


def loaded_from(status: int, output: str) -> Loaded:
    """Build the input the reviewer reads out of the verdict the loader check gave.

    :param status: the command's exit status, nought for exactly the runs where the workflow loaded
    :param output: stdout and stderr as the check printed them, interleaved
    :return: the verdict, its output cut to the tail `OUTPUT_KEPT` admits and marked if it was
    """
    kept = output[-OUTPUT_KEPT:]
    return Loaded(
        passed=status == 0, status=status, output=kept, truncated=len(kept) != len(output)
    )


def record_design() -> ReportingTool[Design]:
    return reporting_tool(
        "record_design",
        "Record the shape you are proposing. Call it exactly once, at the end of your turn.",
        Design,
    )


def record_review() -> ReportingTool[Review]:
    return reporting_tool(
        "record_review",
        "Record this review's findings. Call it exactly once, at the end, even when there are none.",
        Review,
    )


@role(model=Claude.OPUS, accepts=(str, Design, Changes))
def designer(watch: ActivityReporter, ask: Tool) -> Role[Design]:
    return Role(
        name="design",
        instructions=prompt_file("prompts/design.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask, record_design()),
        on_activity=watch,
    )


@role(model=Claude.SONNET, accepts=(Design, Review))
def builder(watch: ActivityReporter, ask: Tool) -> Role[None]:
    return Role(
        name="build",
        instructions=prompt_file("prompts/build.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask,),
        on_activity=watch,
    )


@role(model=Claude.OPUS, accepts=(Design, Loaded))
def reviewer(watch: ActivityReporter, ask: Tool) -> Role[Review]:
    return Role(
        name="review",
        instructions=prompt_file("prompts/review.md"),
        restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES},
        tools=(ask, record_review()),
        on_activity=watch,
    )
