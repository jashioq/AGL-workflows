import sys
from dataclasses import dataclass
from pathlib import Path
from agl.sdk import (
    ActivityReporter,
    Claude,
    ClaudeEffort,
    ReportingTool,
    Restriction,
    Role,
    Tool,
    VerifierOutcome,
    describe,
    prompt_file,
    reporting_tool,
    role,
)


@dataclass(frozen=True, slots=True)
class Design:
    name: str = describe("the workflow's name, lower_snake_case: its directory, module and command")
    diagram: str = describe("the shape in plain characters, at most 70 columns wide")
    summary: str = describe("at most four lines of 70 characters: the decisions behind the shape")


@dataclass(frozen=True, slots=True)
class Changes:
    asked: str


@dataclass(frozen=True, slots=True)
class Review:
    findings: list[str] = describe(
        "each finding as one markdown item saying where and what is wrong; empty when there are none"
    )


@dataclass(frozen=True, slots=True)
class Asked:
    question: str = describe("what you are asking, in full")
    options: tuple[str, ...] = describe("answers to offer, each worded as the answer", default=())


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


def loader_check(name: str) -> str:
    # The agl running this workflow, since one started as .venv/bin/agl puts nothing on PATH
    agl = Path(sys.executable).with_name("agl")
    # A throwaway AGL_HOME, so loading the new workflow never installs it into the user's own
    return (
        f'export AGL_HOME="$(mktemp -d)" && trap \'rm -rf "$AGL_HOME"\' EXIT && mkdir -p '
        f'"$AGL_HOME/workspace/workflows" && cp -R {name} "$AGL_HOME/workspace/workflows" && '
        f"{agl} workflows && {agl} workflows {name}"
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(str, Design, Changes))
def designer(watch: ActivityReporter, ask: Tool) -> Role[Design]:
    return Role(
        name="design",
        instructions=prompt_file("prompts/design.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask, record_design()),
        on_activity=watch,
    )


@role(model=Claude.SONNET(effort=ClaudeEffort.MEDIUM), accepts=(Design, Review))
def builder(watch: ActivityReporter, ask: Tool) -> Role[None]:
    return Role(
        name="build",
        instructions=prompt_file("prompts/build.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask,),
        on_activity=watch,
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Design, VerifierOutcome))
def reviewer(watch: ActivityReporter, ask: Tool) -> Role[Review]:
    return Role(
        name="review",
        instructions=prompt_file("prompts/review.md"),
        restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES},
        tools=(ask, record_review()),
        on_activity=watch,
    )
