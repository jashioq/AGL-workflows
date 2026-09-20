import asyncio
from dataclasses import dataclass
from typing import Final
from agl.sdk import (
    Claude,
    ClaudeEffort,
    OpenAI,
    OpenAIEffort,
    Restriction,
    Role,
    Tool,
    ToolResult,
    describe,
    prompt_file,
    role,
    tool,
)
from .display import BLUE, ORANGE, quiet, said, waiting

HAIKU: Final = "Haiku"
# Short for the `gpt-5.6-luna` the OpenAI adapter's slug table asks its CLI for - the prompts
# still name the model in full, because each of these two is told which model the other is
LUNA: Final = "Luna"

EVERYTHING: Final = frozenset(Restriction)

OVER: Final = "The chat is over. Say nothing more, and end your turn now."
OPENING: Final = "Nothing has been said yet. You open this chat, so say your line."
TWICE: Final = "You said the last line yourself. Listen for an answer before you say another."

OPENS: Final = HAIKU
COLOUR: Final = {HAIKU: ORANGE, LUNA: BLUE}

# The one who opens is thinking from the moment the run starts, with nothing said for it to answer
waiting(COLOUR[OPENS], OPENS)

transcript: list[str] = []
gone: set[str] = set()
# One event a side, set by the other one's `say`, so a waiter is never woken by its own line
turn: Final = {HAIKU: asyncio.Event(), LUNA: asyncio.Event()}


@dataclass(frozen=True, slots=True)
class Line:
    message: str = describe(
        "your next line in the chat: 200 characters at most, one sentence, no name in front of it"
    )


# `listen` takes no arguments, and a tool payload is a dataclass whatever it carries
@dataclass(frozen=True, slots=True)
class Nothing:
    ...


# A session that ends frees the other side from its `listen`, or that one waits on a line nobody
# is left to say - however it ended, and whether it got as far as the cap or not
def ended(name: str) -> None:
    quiet()
    gone.add(name)
    turn[_other(name)].set()


def says(name: str, cap: int) -> Tool:
    async def spoken(line: Line) -> ToolResult:
        if len(transcript) >= cap:
            return ToolResult(text=OVER, rejected=True)
        if transcript and transcript[-1].startswith(f"{name}:"):
            return ToolResult(text=TWICE, rejected=True)
        transcript.append(f"{name}: {line.message}")
        said(COLOUR[name], name, line.message)
        # Woken whether the cap has just been reached or not: the other side is waiting on this
        # event either for a line to answer or to be told the chat is over
        other = _other(name)
        turn[other].set()
        if len(transcript) >= cap:
            quiet()
            return ToolResult(text=OVER)
        waiting(COLOUR[other], other)
        return ToolResult(text="Said. Now listen for the answer.")

    return tool("say", "Say your next line, which is how the other one hears you.", Line, spoken)


def listens(name: str, cap: int) -> Tool:
    async def heard(_: Nothing) -> ToolResult:
        # Nothing would ever wake the one who opens, so it is told to speak rather than left to
        # wait on a line the other one is itself waiting for
        if not transcript and name == OPENS:
            return ToolResult(text=OPENING)
        await turn[name].wait()
        turn[name].clear()
        if len(transcript) >= cap or _other(name) in gone:
            return ToolResult(text=OVER)
        return ToolResult(text=transcript[-1])

    return tool(
        "listen",
        "Wait for the other one to say something, and read it. Takes no arguments.",
        Nothing,
        heard,
    )


def _other(name: str) -> str:
    return LUNA if name == HAIKU else HAIKU


# Haiku advertises no effort levels at all, so the CLI drops this one - written because a model
# named without an effort runs at whatever its tool defaults to, which nobody here chose
@role(model=Claude.HAIKU(effort=ClaudeEffort.LOW), accepts=(str,))
def haiku_speaker(cap: int) -> Role[None]:
    return Role(
        name="haiku",
        instructions=prompt_file("prompts/haiku.md"),
        tools=(says(HAIKU, cap), listens(HAIKU, cap)),
    )


# `low` is the bottom of what this model offers - its listing starts there and has no `minimal`
@role(model=OpenAI.LUNA(effort=OpenAIEffort.LOW), accepts=(str,))
def luna_speaker(cap: int) -> Role[None]:
    return Role(
        name="luna",
        instructions=prompt_file("prompts/luna.md"),
        tools=(says(LUNA, cap), listens(LUNA, cap)),
    )
