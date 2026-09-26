import asyncio
from agl.sdk import Run
from .display import display
from .roles import Ticket


def target[P](run: Run[P], ticket: Ticket) -> Run[P]:
    return run.worktree(ticket.parent) if ticket.parent else run


def checkout[P](run: Run[P], ticket: Ticket) -> Run[P]:
    return target(run, ticket).worktree(ticket.name)


async def land[P](run: Run[P], ticket: Ticket) -> None:
    """Merge a ticket's branch into the one it was cut from, waiting out any conflict.

    The project's build must pass in the target first; a conflict is put on screen and retried."""
    name, child = ticket.name, checkout(run, ticket)
    landing = await child.integrate()
    while landing.conflicted:
        if landing.refused_by_the_gate:
            display.refused(name, (await child.verify("pwd")).output.strip())
        else:
            display.conflicted(name, (await target(run, ticket).verify("pwd")).output.strip())
        await asyncio.sleep(5)
        await landing.retry()
    display.cleared(name)
