import asyncio
from dataclasses import dataclass, replace
from typing import Final
from agl.sdk import Role, Run, Stop, arg, workflow
from .branches import checkout, land
from .display import display
from .roles import (
    History,
    Ticket,
    Triage,
    builder,
    interviewer,
    raised,
    remember,
    spec_reviewer,
    splitter,
    standards_reviewer,
    triager,
    watch,
)
from .turns import Turns

MAX_CONCURRENT_TICKETS: Final = 3
MAX_REVIEW_ROUNDS: Final = 3


@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what you want built")


interviewing = interviewer()
splitting = splitter()
building = builder()
spec_reviewing = spec_reviewer()
standards_reviewing = standards_reviewer()
triaging = triager()


@workflow
async def ticket_split(run: Run[Parameters]) -> None:
    """Turn what the person asked for into a spec, split it into tickets, and build them all."""
    await display.open(run.terminal, str(run.scope.label))

    display.phase("Interview")
    spec = await run.step(interviewing, run.params.request)
    remember(spec)

    display.phase("Split tickets")
    tickets = await run.step(splitting, spec)

    display.phase("Build")
    await work_every(Turns(MAX_CONCURRENT_TICKETS), run, tickets.tickets)


async def work_every(turns: Turns, run: Run[Parameters], tickets: list[Ticket]) -> None:
    """Work every ticket given, each in its own task, returning once all of them have landed.

    Serves both the tickets the split produced and the tickets a review raises."""
    async with asyncio.TaskGroup() as group:
        for ticket in tickets:
            display.pending(ticket.name, ticket.parent)
            group.create_task(work_on(turns, run, ticket))


async def work_on(turns: Turns, run: Run[Parameters], ticket: Ticket) -> None:
    """Carry one ticket from its first build through its reviews to its merge.

    Every round's triage is kept, so the next one can tell a finding it has seen before."""
    rounds: list[Triage] = []
    for round_number in range(MAX_REVIEW_ROUNDS):
        async with turns.turn(ticket):
            display.working(ticket.name)
            if not round_number:
                await build(run, ticket)
            if ticket.parent:
                break
            triaged = await review(run, ticket, History(rounds))
        if not triaged.bugs:
            break
        if round_number == MAX_REVIEW_ROUNDS - 1:
            raise Stop(unfinished(ticket.name, triaged.bugs))
        bugs = raised(ticket, triaged.bugs, rounds)
        rounds = [*rounds, replace(triaged, bugs=bugs)]
        display.waiting(ticket.name)
        await work_every(turns, run, bugs)

    display.waiting(ticket.name)
    await land(run, ticket)
    display.merged(ticket.name)
    await turns.landed(ticket.name)


async def build(run: Run[Parameters], ticket: Ticket) -> None:
    """Ask an agent to make the ticket true in its own checkout, and commit what it wrote.

    The project's build command goes in with it, because that is what its merge is judged on."""
    await checkout(run, ticket).step(
        watch(building, ticket.name),
        ticket,
        run.config["build"],
        commit=f"build {ticket.name}",
    )


async def review(run: Run[Parameters], ticket: Ticket, history: History) -> Triage:
    """Read a ticket's work on both axes at once and decide which findings still have to be done.

    Each axis is a step with a context of its own, and a third triages findings against what the
    earlier rounds raised. Steps in one checkout take turns, so the standards axis, which only
    reads git, gets a checkout of its own cut from the ticket's, a fresh one each round to see
    that round's work. The spec axis stays in the ticket's, where its build has already run."""
    child, name, gate = checkout(run, ticket), ticket.name, run.config["build"]
    aside = child.worktree(f"{name}-standards-{len(history.rounds) + 1}")
    async with asyncio.TaskGroup() as group:
        spec = group.create_task(reading(child, spec_reviewing, name, "spec", ticket, gate))
        standards = group.create_task(
            reading(aside, standards_reviewing, name, "standards", ticket)
        )
    return await reading(
        child, triaging, name, "triage", ticket, spec.result(), standards.result(), history, gate
    )


async def reading[R](
    run: Run[Parameters], role: Role[R], ticket: str, agent: str, *inputs: object
) -> R:
    """Take one review step, showing its agent and timer on the ticket's row while it runs."""
    with display.reviewing(ticket, agent):
        return await run.step(watch(role, ticket), *inputs)


def unfinished(name: str, bugs: list[Ticket]) -> str:
    """Say what a review still wanted after the last round it was allowed."""
    wanted = "\n".join(f"- {bug.name}: {bug.builds}" for bug in bugs)
    return f"{MAX_REVIEW_ROUNDS} reviews of {name} and the last one still found work:\n\n{wanted}"
