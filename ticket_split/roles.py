import json
from dataclasses import asdict, dataclass
from agl.sdk import (
    Claude,
    ClaudeEffort,
    Restriction,
    Role,
    ToolResult,
    describe,
    prompt_file,
    reporting_tool,
    role,
    tool,
)
from .display import answer, report


@dataclass(frozen=True, slots=True)
class Spec:
    problem: str = describe("the problem the user is facing, from the user's perspective")
    solution: str = describe("the solution to that problem, from the user's perspective")
    stories: list[str] = describe(
        "a long list of user stories, each `As an <actor>, I want a <feature>, so that <benefit>`"
    )
    seams: list[str] = describe(
        "one line per seam the feature will be tested at, and whether it already exists"
    )
    implementation: list[str] = describe(
        "one decision per line: modules, interfaces, architecture, schema, API contracts; no file "
        "paths and no code, except a snippet from a prototype that encodes a decision precisely"
    )
    testing: list[str] = describe(
        "one decision per line: what makes a good test here, which modules are tested, prior art"
    )
    out_of_scope: str = describe("what this spec deliberately does not cover")
    terms: list[str] = describe(
        "the glossary, one term per line as `Term: one or two sentences. Avoid: <synonyms>`; only "
        "terms this project's domain owns, never general programming concepts"
    )
    decisions: list[str] = describe(
        "one ADR per line as `Title: 1-3 sentences saying the context, the decision and why`; only "
        "decisions that are hard to reverse, surprising without context and a real trade-off"
    )
    notes: str = describe("anything else worth knowing about the feature", default="")


@dataclass(frozen=True, slots=True)
class Ticket:
    name: str = describe(
        "a short name in lower case with words joined by hyphens - letters, digits and hyphens "
        "only, no spaces, unique among every ticket here: it names this ticket's branch"
    )
    builds: str = describe(
        "the end-to-end behaviour this ticket makes work, from the user's perspective, never a "
        "layer-by-layer implementation list"
    )
    criteria: list[str] = describe(
        "one acceptance criterion per line, each one false at the commit this ticket starts from"
    )
    blocked_by: tuple[str, ...] = describe(
        "the names of the tickets that must finish before this one can start; empty when it can "
        "start immediately",
        default=(),
    )


@dataclass(frozen=True, slots=True)
class Tickets:
    tickets: list[Ticket] = describe("every ticket, in dependency order with blockers first")


@dataclass(frozen=True, slots=True)
class SpecReview:
    findings: list[str] = describe(
        "one finding per line, each quoting the line of the ticket or the spec it is about; empty "
        "when there are none"
    )


@dataclass(frozen=True, slots=True)
class StandardsReview:
    findings: list[str] = describe(
        "one finding per line, each citing the standards file and its rule, or naming one baseline "
        "smell and quoting the hunk; empty when there are none"
    )


@dataclass(frozen=True, slots=True)
class Triage:
    fix: list[str] = describe(
        "every finding that is real and belongs in the worktree under review, each rewritten so "
        "the builder can act on that line alone; empty when nothing has to change"
    )
    bugs: list[Ticket] = describe(
        "one ticket per finding that is real and does not belong in the worktree under review; "
        "empty when there is none"
    )


@dataclass(frozen=True, slots=True)
class Asked:
    question: str = describe("what you are asking, in full; a round of questions goes here as one")
    options: tuple[str, ...] = describe("answers to offer, each worded as the answer", default=())


# `read_the_spec` takes no arguments, and a tool payload is a dataclass whatever it carries
@dataclass(frozen=True, slots=True)
class Nothing:
    ...


# A tool handler is handed its payload and nothing else, so the spec reaches one this way
spec_recorded: Spec


def remember(spec: Spec) -> None:
    global spec_recorded
    spec_recorded = spec


async def answered(asked: Asked) -> ToolResult:
    said = await answer(asked.question, asked.options)
    return ToolResult(text=said or "They typed nothing, so use your own judgement.")


async def handed_over(_: Nothing) -> ToolResult:
    return ToolResult(text=json.dumps(asdict(spec_recorded), indent=2))


ask = tool(
    "ask_the_person",
    "Ask the person running this workflow a question, and wait for their answer.",
    Asked,
    answered,
)

read_the_spec = tool(
    "read_the_spec",
    "Read the spec every ticket in this run came out of, as a JSON object. Takes no arguments.",
    Nothing,
    handed_over,
)

record_spec = reporting_tool(
    "record_spec",
    "Record the spec. Call it exactly once, after the interview has nothing left to ask.",
    Spec,
)

record_tickets = reporting_tool(
    "record_tickets",
    "Record the tickets the person approved. Call it exactly once, after they approve.",
    Tickets,
)

record_spec_review = reporting_tool(
    "record_spec_review",
    "Record the Spec axis. Call it exactly once, at the end, even when you found nothing.",
    SpecReview,
)

record_standards_review = reporting_tool(
    "record_standards_review",
    "Record the Standards axis. Call it exactly once, at the end, even when you found nothing.",
    StandardsReview,
)

record_triage = reporting_tool(
    "record_triage",
    "Record what the builder fixes here and what becomes a ticket of its own. Call it once.",
    Triage,
)


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(str,))
def interviewer() -> Role[Spec]:
    return Role(
        name="interview",
        instructions=prompt_file("prompts/interview.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
        },
        tools=(ask, record_spec),
        on_activity=report,
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Spec,))
def splitter() -> Role[Tickets]:
    return Role(
        name="split",
        instructions=prompt_file("prompts/split.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
            Restriction.NO_SHELL,
            Restriction.NO_NETWORK,
        },
        tools=(ask, record_tickets),
        on_activity=report,
    )


@role(model=Claude.SONNET(effort=ClaudeEffort.HIGH), accepts=(Ticket, Triage, str))
def builder() -> Role[None]:
    return Role(
        name="build",
        instructions=prompt_file("prompts/build.md"),
        restrictions={Restriction.NO_VCS_WRITES},
        tools=(ask, read_the_spec),
    )


@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Ticket, str))
def spec_reviewer() -> Role[SpecReview]:
    return Role(
        name="spec-review",
        instructions=prompt_file("prompts/spec_review.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
            Restriction.NO_NETWORK,
        },
        tools=(ask, read_the_spec, record_spec_review),
    )


# No `read_the_spec`: this axis is the repository's own conventions, and the spec is the other's
@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(Ticket,))
def standards_reviewer() -> Role[StandardsReview]:
    return Role(
        name="standards-review",
        instructions=prompt_file("prompts/standards_review.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
            Restriction.NO_NETWORK,
        },
        tools=(ask, record_standards_review),
    )


@role(
    model=Claude.OPUS(effort=ClaudeEffort.HIGH),
    accepts=(Ticket, SpecReview, StandardsReview, str),
)
def triager() -> Role[Triage]:
    return Role(
        name="triage",
        instructions=prompt_file("prompts/triage.md"),
        restrictions={
            Restriction.NO_FILE_WRITES,
            Restriction.NO_VCS_WRITES,
            Restriction.NO_NETWORK,
        },
        tools=(ask, read_the_spec, record_triage),
    )
