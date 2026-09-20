import asyncio
from dataclasses import dataclass
from typing import Final
from agl.sdk import Role, Run, Stop, arg, workflow
from .display import opened
from .roles import HAIKU, LUNA, ended, haiku_speaker, luna_speaker, transcript

MAX_TURNS: Final = 20


@dataclass(frozen=True, slots=True)
class Parameters:
    topic: str = arg("-r", "--topic", help="what the two of them talk about")


talking_haiku = haiku_speaker(MAX_TURNS)
talking_luna = luna_speaker(MAX_TURNS)


@workflow
async def chat(run: Run[Parameters]) -> None:
    await opened(run.terminal, f"{HAIKU} and {LUNA}'s chat")

    async with asyncio.TaskGroup() as group:
        group.create_task(talking(run, talking_haiku, HAIKU))
        group.create_task(talking(run, talking_luna, LUNA))

    raise Stop(f"the chat ended after {len(transcript)} of the {MAX_TURNS} lines it is capped at")


async def talking(run: Run[Parameters], speaking: Role[None], name: str) -> None:
    try:
        await run.worktree(name.lower()).step(speaking, run.params.topic)
    finally:
        ended(name)
