import asyncio
from dataclasses import dataclass
from typing import Final
from agl.sdk import (
    Claude,
    ClaudeEffort,
    OpenAI,
    OpenAIEffort,
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
LUNA: Final = "Luna"

OVER: Final = "The chat is over. Say nothing more, and end your turn now."
OPENING: Final = "Nothing has been said yet. You open this chat, so say your line."
NOT_YOUR_TURN: Final = "It is not your turn. Listen for the other one's line before you say yours."

OPENS: Final = HAIKU
COLOUR: Final = {HAIKU: ORANGE, LUNA: BLUE}


@dataclass(frozen=True, slots=True)
class Line:
    message: str = describe(
        "your next line in the chat: 200 characters at most, no name in front of it"
    )


class Conversation:
    """What has been said so far, and whose turn it is to say the next line."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.lines: list[str] = []
        self.over = False
        # Set while it is that side's turn to speak, which is what its `listen` waits for
        self.turn = {HAIKU: asyncio.Event(), LUNA: asyncio.Event()}
        self._hand_to(OPENS)

    def tools(self, name: str) -> tuple[Tool, Tool]:
        say = tool(
            "say",
            "Say your next line, which is how the other one hears you.",
            Line,
            lambda line: self.say(name, line.message),
        )
        listen = Tool(
            name="listen",
            description="Wait for the other one to say something, and read it. Takes no arguments.",
            payload_schema={"type": "object", "properties": {}},
            handler=lambda _: self.listen(name),
        )
        return say, listen

    async def say(self, name: str, message: str) -> ToolResult:
        if self.over:
            return ToolResult(text=OVER, rejected=True)
        if not self.turn[name].is_set():
            return ToolResult(text=NOT_YOUR_TURN, rejected=True)
        self.turn[name].clear()
        self.lines.append(f"{name}: {message}")
        said(COLOUR[name], name, message)
        if len(self.lines) >= self.limit:
            self.end()
            return ToolResult(text=OVER)
        self._hand_to(_other(name))
        return ToolResult(text="Said. Now listen for the answer.")

    async def listen(self, name: str) -> ToolResult:
        await self.turn[name].wait()
        if self.over:
            return ToolResult(text=OVER)
        if not self.lines:
            return ToolResult(text=OPENING)
        return ToolResult(text=self.lines[-1])


    def end(self) -> None:
        self.over = True
        quiet()
        for turn in self.turn.values():
            turn.set()

    def _hand_to(self, name: str) -> None:
        self.turn[name].set()
        waiting(COLOUR[name], name)


def _other(name: str) -> str:
    return LUNA if name == HAIKU else HAIKU


@role(model=Claude.HAIKU(effort=ClaudeEffort.LOW), accepts=(str,))
def haiku_speaker(conversation: Conversation) -> Role[None]:
    return Role(
        name="haiku",
        instructions=prompt_file("prompts/haiku.md"),
        tools=conversation.tools(HAIKU),
    )


@role(model=OpenAI.LUNA(effort=OpenAIEffort.LOW), accepts=(str,))
def luna_speaker(conversation: Conversation) -> Role[None]:
    return Role(
        name="luna",
        instructions=prompt_file("prompts/luna.md"),
        tools=conversation.tools(LUNA),
    )
