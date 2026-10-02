from dataclasses import dataclass
from agl.sdk import Run, arg, workflow
from .display import finished, opened, planned, started
from .roles import splitter, worker


@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="what you want built")
    stages: int = arg("-s", "--stages", help="how many stages to split it into")


splitting = splitter()
working = worker()


@workflow
async def in_stages(run: Run[Parameters]) -> None:
    request = run.params.request
    await opened(run.terminal, run.label, run.params.stages)

    plan = await run.step(splitting, request, run.params.stages)
    planned([stage.name for stage in plan.stages])

    # On a resume every stage that finished is replayed from the record, so the loop runs straight
    # through them and the first agent to start is the one for the stage that was cut short
    for number, stage in enumerate(plan.stages):
        started(number)
        await run.step(working, request, plan, stage, commit=f"stage {number + 1}: {stage.name}")
        finished(number)
