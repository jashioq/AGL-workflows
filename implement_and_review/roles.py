from dataclasses import dataclass
from agl.sdk import (
    ActivityReporter,
    Claude,
    OpenAI,
    ReportingTool,
    Restriction,
    Role,
    describe,
    prompt_file,
    reporting_tool,
    role,
)


@dataclass(frozen=True, slots=True)
class Review:
    findings: list[str] = describe(
        "each finding as one markdown item saying where and what is wrong; empty when there are none"
    )


def record_review() -> ReportingTool[Review]:
    return reporting_tool(
        "record_review",
        "Record this review's findings. Call it exactly once, at the end, even when there are none.",
        Review,
    )


@role(model=Claude.OPUS, accepts=(str, Review))
def implementer(watch: ActivityReporter) -> Role[None]:
    return Role(
        name="implement",
        instructions=prompt_file("prompts/implement.md"),
        on_activity=watch,
    )


@role(model=OpenAI.SOL, accepts=(str,))
def reviewer(watch: ActivityReporter) -> Role[Review]:
    return Role(
        name="review",
        instructions=prompt_file("prompts/review.md"),
        restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES},
        tools=(record_review(),),
        on_activity=watch,
    )
