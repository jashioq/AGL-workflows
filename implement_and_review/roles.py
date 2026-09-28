from dataclasses import dataclass
from agl.sdk import (
    ActivityReporter,
    Claude,
    ClaudeEffort,
    OpenAI,
    OpenAIEffort,
    ReportingTool,
    Restriction,
    Role,
    Tool,
    ToolResult,
    describe,
    prompt_file,
    reporting_tool,
    role,
    tool,
)
from .display import answer


@dataclass(frozen=True, slots=True)
class Review:
    findings: list[str] = describe(
        "each finding as one markdown item saying where and what is wrong; empty when there are none"
    )


@dataclass(frozen=True, slots=True)
class Asked:
    question: str = describe("what you are asking, in full; one question per call, never several")
    options: tuple[str, ...] = describe("answers to offer, each worded as the answer", default=())


async def answered(asked: Asked) -> ToolResult:
    said = await answer(asked.question, asked.options)
    return ToolResult(text=said)


def ask_question() -> Tool:
    return tool(
        "ask_question",
        "Ask the person running this workflow a question, and wait for their answer.",
        Asked,
        answered,
    )


def record_review() -> ReportingTool[Review]:
    return reporting_tool(
        "record_review",
        "Record this review's findings. Call it exactly once, at the end, even when there are none.",
        Review,
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.MEDIUM), accepts=(str, Review))
def implementer(watch: ActivityReporter) -> Role[None]:
    return Role(
        name="implement",
        instructions=prompt_file("prompts/implement.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask_question(),),
        on_activity=watch,
    )


@role(model=OpenAI.SOL(effort=OpenAIEffort.MEDIUM), accepts=(str,))
def reviewer(watch: ActivityReporter) -> Role[Review]:
    return Role(
        name="review",
        instructions=prompt_file("prompts/review.md"),
        restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES},
        tools=(ask_question(), record_review()),
        on_activity=watch,
    )
