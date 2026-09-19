from dataclasses import dataclass
from functools import partial
from pathlib import Path
import agl.sdk
from agl.sdk import (
    Claude,
    ClaudeEffort,
    Restriction,
    Role,
    ToolResult,
    VerifierOutcome,
    describe,
    prompt_file,
    reporting_tool,
    role,
    tool,
)
from .display import answer, report


@dataclass(frozen=True, slots=True)
class Spec:
    name: str = describe("the workflow's name, lower_snake_case: its directory, module and command")
    does: str = describe("what the workflow does and who runs it, in a paragraph")
    shape: str = describe(
        "the diagram, plain characters at most 70 columns wide, then one line per step in the "
        "order it runs: its role, what it is handed, what it reports, what it commits; no code"
    )
    roles: list[str] = describe(
        "one line per role: its name, model and effort, and every restriction"
    )
    decisions: list[str] = describe(
        "what the person decided: each design they turned down and why, each thing they said matters"
    )


@dataclass(frozen=True, slots=True)
class Review:
    findings: list[str] = describe(
        "each finding as one markdown item saying where and what is wrong; empty when there are none"
    )


@dataclass(frozen=True, slots=True)
class Asked:
    question: str = describe("what you are asking, in full; a design is shown here line by line")
    options: tuple[str, ...] = describe("answers to offer, each worded as the answer", default=())


async def answered(asked: Asked) -> ToolResult:
    said = await answer(asked.question, asked.options)
    return ToolResult(text=said or "They typed nothing, so use your own judgement.")


ask = tool(
    "ask_the_person",
    "Ask the person running this workflow a question, and wait for their answer.",
    Asked,
    answered,
)

record_spec = reporting_tool(
    "record_spec",
    "Record the spec of the design the person approved. Call it exactly once, after they approve.",
    Spec,
)

record_review = reporting_tool(
    "record_review",
    "Record this review's findings. Call it exactly once, at the end, even when there are none.",
    Review,
)


def instructions(prompt: str, guidelines: str) -> str:
    # The agent works in the run's checkout, which holds neither the guidelines nor the SDK
    sdk = Path(agl.sdk.__file__).parent
    return (
        f"{prompt_file(prompt)}\n{prompt_file(guidelines)}\n"
        f"The AGL SDK this run is on is {sdk}. Read it there, never a copy of AGL found elsewhere.\n"
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(str,))
def designer() -> Role[Spec]:
    return Role(
        name="design",
        instructions=instructions("prompts/design.md", "BUILDER_GUIDELINES.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
        },
        tools=(ask, record_spec),
        on_activity=partial(report, "design"),
    )


@role(model=Claude.SONNET(effort=ClaudeEffort.HIGH), accepts=(Spec, Review))
def builder() -> Role[None]:
    return Role(
        name="build",
        instructions=instructions("prompts/build.md", "BUILDER_GUIDELINES.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        on_activity=partial(report, "build"),
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Spec, VerifierOutcome))
def build_reviewer() -> Role[Review]:
    return Role(
        name="build-review",
        instructions=instructions("prompts/build_review.md", "BUILDER_GUIDELINES.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
        },
        tools=(record_review,),
        on_activity=partial(report, "build-review"),
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Spec, Review))
def cleaner() -> Role[None]:
    return Role(
        name="clean",
        instructions=instructions("prompts/clean.md", "CLEANER_GUIDELINES.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        on_activity=partial(report, "clean"),
    )


# Keeps its shell for the one thing it cannot judge without: git diff of what cleaning changed
@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Spec, VerifierOutcome))
def clean_reviewer() -> Role[Review]:
    return Role(
        name="clean-review",
        instructions=instructions("prompts/clean_review.md", "CLEANER_GUIDELINES.md"),
        restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES},
        tools=(record_review,),
        on_activity=partial(report, "clean-review"),
    )
