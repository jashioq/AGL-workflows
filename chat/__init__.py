import asyncio
from dataclasses import dataclass
from agl.sdk import Role, Run, Stop, arg, workflow
from .display import opened
from .roles import HAIKU, LUNA, Conversation, haiku_speaker, luna_speaker


@dataclass(frozen=True, slots=True)
class Parameters:
    topic: str = arg("-r", "--topic", help="what the two of them talk about")
    lines: int = arg("-l", "--lines", default=20, help="how many lines the chat ends after")


@workflow
async def chat(run: Run[Parameters]) -> None:
    await opened(run.terminal, f"{HAIKU} and {LUNA}'s chat")

    conversation = Conversation(run.params.lines)
    async with asyncio.TaskGroup() as group:
        group.create_task(talking(run, conversation, haiku_speaker(conversation)))
        group.create_task(talking(run, conversation, luna_speaker(conversation)))

    raise Stop(
        f"the chat ended after {len(conversation.lines)} of the {conversation.limit} lines it is "
        f"capped at"
    )


async def talking(run: Run[Parameters], conversation: Conversation, speaking: Role[None]) -> None:
    try:
        await run.worktree(speaking.name).step(speaking, run.params.topic)
    finally:
        conversation.end()
