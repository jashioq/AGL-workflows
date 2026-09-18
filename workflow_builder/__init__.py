import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from agl.sdk import Role, Run, Stop, arg, workflow
from .display import began, opened, report
from .roles import (
    Review,
    Spec,
    build_reviewer,
    builder,
    clean_reviewer,
    cleaner,
    designer,
)

MAX_ROUNDS: Final = 3


@dataclass(frozen=True, slots=True)
class Parameters:
    request: str = arg("-r", "--request", help="the workflow you want built")


designing = designer()
building = builder()
reviewing_build = build_reviewer()
cleaning = cleaner()
reviewing_clean = clean_reviewer()


@workflow
async def workflow_builder(run: Run[Parameters]) -> None:
    await opened(run.terminal)

    began(designing)
    spec = await run.step(designing, run.params.request)

    began(building)
    await run.step(building, spec, commit=f"build {spec.name}")

    # Review loop
    for round_number in range(MAX_ROUNDS):
        review = await reviewed(run, reviewing_build, spec)
        if not review.findings:
            break
        if round_number == MAX_ROUNDS - 1:
            findings = "\n".join(review.findings)
            raise Stop(
                f"{MAX_ROUNDS} build reviews and the last one still had findings:\n\n{findings}"
            )
        began(building)
        await run.step(
            building,
            spec,
            review,
            commit=f"fix what build review round {round_number + 1} found",
        )

    began(cleaning)
    await run.step(cleaning, spec, commit=f"clean up {spec.name}")
    for round_number in range(MAX_ROUNDS):
        review = await reviewed(run, reviewing_clean, spec)
        if not review.findings:
            break
        if round_number == MAX_ROUNDS - 1:
            findings = "\n".join(review.findings)
            raise Stop(
                f"{MAX_ROUNDS} clean reviews and the last one still had findings:\n\n{findings}"
            )
        began(cleaning)
        await run.step(
            cleaning,
            spec,
            review,
            commit=f"fix what clean review round {round_number + 1} found",
        )


async def reviewed(run: Run[Parameters], reviewing: Role[Review], spec: Spec) -> Review:
    report("agl", f"agl workflows {spec.name}")
    loaded = await run.verify(loader_check(spec.name))
    began(reviewing)
    return await run.step(reviewing, spec, loaded)


def loader_check(name: str) -> str:
    # The agl running this workflow, since one started as .venv/bin/agl puts nothing on PATH
    agl = Path(sys.executable).with_name("agl")
    # A throwaway AGL_HOME, so loading the new workflow never installs it into the user's own
    return (
        f'export AGL_HOME="$(mktemp -d)" && trap \'rm -rf "$AGL_HOME"\' EXIT && mkdir -p '
        f'"$AGL_HOME/workspace/workflows" && cp -R {name} "$AGL_HOME/workspace/workflows" && '
        f"{agl} workflows && {agl} workflows {name}"
    )
