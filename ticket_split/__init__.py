import asyncio
from dataclasses import dataclass, replace
from typing import Final
from agl.sdk import Run, Stop, arg, workflow
from .display import (
    MERGED,
    RUNNING,
    WAITING,
    at,
    conflicting,
    entered,
    gate_refused,
    listed,
    opened,
    resolved,
    watching,
)
from .roles import (
    Ticket,
    builder,
    interviewer,
    remember,
    spec_reviewer,
    splitter,
    standards_reviewer,
    triager,
)

MAX_CONCURRENT_TICKETS: Final = 3
MAX_REVIEW_ROUNDS: Final = 3


@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what you want built")


interviewing = interviewer()
splitting = splitter()
# Bound here so `agl workflows` checks their prompts, and copied per ticket for its own activity
building = builder()
spec_reviewing = spec_reviewer()
standards_reviewing = standards_reviewer()
triaging = triager()


@workflow
async def ticket_split(run: Run[Parameters]) -> None:
    await opened(run.terminal, str(run.scope.label))

    entered("Interview")
    spec = await run.step(interviewing, run.params.request)
    # Every later role may need the spec and none always does, so it is a tool and not an input
    remember(spec)

    entered("Split tickets")
    tickets = await run.step(splitting, spec)

    entered("Build")
    slots = asyncio.Semaphore(MAX_CONCURRENT_TICKETS)
    landed = {ticket.name: asyncio.Event() for ticket in tickets.tickets}
    async with asyncio.TaskGroup() as group:
        for ticket in tickets.tickets:
            listed(ticket.name)
            group.create_task(worked(run, ticket, slots, landed))


async def worked(
    target: Run[Parameters],
    ticket: Ticket,
    slots: asyncio.Semaphore,
    landed: dict[str, asyncio.Event],
) -> None:
    for blocker in ticket.blocked_by:
        await landed[blocker].wait()

    bugs: list[Ticket] = []
    async with slots:
        child = target.worktree(ticket.name)
        at(ticket.name, RUNNING)
        builds = replace(building, on_activity=watching(ticket.name))
        against_spec = replace(spec_reviewing, on_activity=watching(ticket.name))
        against_standards = replace(standards_reviewing, on_activity=watching(ticket.name))
        triages = replace(triaging, on_activity=watching(ticket.name))
        gate = target.config["build"]
        await child.step(builds, ticket, gate, commit=f"build {ticket.name}")
        for round_number in range(MAX_REVIEW_ROUNDS):
            # Two steps rather than one gather: a namespace runs one step at a time, and what the
            # axes buy is a context each rather than the wall clock
            spec = await child.step(against_spec, ticket, gate)
            standards = await child.step(against_standards, ticket)
            triaged = await child.step(triages, ticket, spec, standards, gate)
            # A bug found while reviewing a bug has nowhere further down to be cut from
            if len(child.scope.namespaces) == 1:
                bugs.extend(triaged.bugs)
            if not triaged.fix:
                break
            if round_number == MAX_REVIEW_ROUNDS - 1:
                findings = "\n".join(f"- {one}" for one in triaged.fix)
                raise Stop(
                    f"{MAX_REVIEW_ROUNDS} review rounds on {ticket.name} and triage still "
                    f"wants these fixed:\n\n{findings}"
                )
            await child.step(
                builds,
                ticket,
                triaged,
                gate,
                commit=f"fix what review round {round_number + 1} found on {ticket.name}",
            )

    at(ticket.name, WAITING)
    async with asyncio.TaskGroup() as group:
        for number, bug in enumerate(bugs, start=1):
            # A namespace is run-wide, and nothing outside its parent's branch can gate a bug
            named = replace(bug, name=f"{ticket.name}-{number}-{bug.name}", blocked_by=())
            landed[named.name] = asyncio.Event()
            listed(named.name, ticket.name)
            group.create_task(worked(child, named, slots, landed))

    await merged(target, child, ticket.name)
    at(ticket.name, MERGED)
    landed[ticket.name].set()


async def merged(target: Run[Parameters], child: Run[Parameters], name: str) -> None:
    landing = await child.integrate()
    while landing.conflicted:
        if landing.refused_by_the_gate:
            # The gate undid the landing in the target, so what needs fixing is still this branch
            gate_refused(name, (await child.verify("pwd")).output.strip())
        else:
            conflicting(name, (await target.verify("pwd")).output.strip())
        # A person is answering this, so nothing caps it and nothing else lands here until it ends
        await asyncio.sleep(5)
        await landing.retry()
    resolved(name)
