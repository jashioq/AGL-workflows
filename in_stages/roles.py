from dataclasses import dataclass
from agl.sdk import (
    Claude,
    ClaudeEffort,
    Restriction,
    Role,
    describe,
    prompt_file,
    reporting_tool,
    role,
)


@dataclass(frozen=True, slots=True)
class Stage:
    name: str = describe("what the board calls this stage: two to four words, no full stop")
    builds: str = describe("what this stage builds, in a few sentences another agent can work from")


@dataclass(frozen=True, slots=True)
class Plan:
    stages: list[Stage] = describe("every stage, in the order they are built")


record_plan = reporting_tool(
    "record_plan",
    "Record the stages. Call it exactly once, at the end.",
    Plan,
)


@role(model=Claude.SONNET(effort=ClaudeEffort.MEDIUM), accepts=(str, int))
def splitter() -> Role[Plan]:
    return Role(
        name="split",
        instructions=prompt_file("prompts/split.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(record_plan,),
    )


@role(model=Claude.SONNET(effort=ClaudeEffort.MEDIUM), accepts=(str, Plan, Stage))
def worker() -> Role[None]:
    return Role(
        name="work",
        instructions=prompt_file("prompts/work.md"),
        restrictions={Restriction.NO_VCS_WRITES},
    )
