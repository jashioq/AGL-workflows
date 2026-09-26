import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from .roles import Ticket


class Turns:
    """Hands out the right to work, so no more tickets run at once than the run allows.

    A ticket waits until everything blocking it has landed; of those ready, review's go first."""
    def __init__(self, at_once: int) -> None:
        self._at_once = at_once
        self._running = 0
        self._queued: list[Ticket] = []
        self._landed: set[str] = set()
        self._moved = asyncio.Condition()

    @asynccontextmanager
    async def turn(self, ticket: Ticket) -> AsyncIterator[None]:
        """Hold the right to work on this ticket for the length of the block.

        Waits until nothing blocks the ticket and a place has come free."""
        async with self._moved:
            self._queued.append(ticket)
            await self._moved.wait_for(lambda: self._first() is ticket)
            self._queued = [one for one in self._queued if one is not ticket]
            self._running += 1
        try:
            yield
        finally:
            async with self._moved:
                self._running -= 1
                self._moved.notify_all()

    async def landed(self, name: str) -> None:
        """Record that a ticket has merged, waking anything that was waiting on it."""
        async with self._moved:
            self._landed.add(name)
            self._moved.notify_all()

    def _first(self) -> Ticket | None:
        """The ticket that should take the next free place, or nothing while none can."""
        if self._running >= self._at_once:
            return None
        ready = [one for one in self._queued if self._unblocked(one)]
        return next(iter([one for one in ready if one.parent] or ready), None)

    def _unblocked(self, ticket: Ticket) -> bool:
        return all(name in self._landed for name in ticket.blocked_by)
