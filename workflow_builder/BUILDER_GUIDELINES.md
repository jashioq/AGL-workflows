# How to build an AGL workflow

Each rule shows what to write and what not to write, taken from real workflows.

## No comments

Write no comments and no docstrings at all, and no README. A comment in what you write is a
finding. Comments are added later by someone reading the finished code.

    yes   MAX_ROUNDS: Final = 3
    no    # Review and fix loop
    no    """Build the tool a role asks its question through, which is the whole of how..."""

## No git

AGL makes the worktree and the branch, commits when a step ends, and on a resume replays a
finished step instead of paying for it again. Nothing you write commits, branches, pushes or
stages, and no prompt you write asks an agent to. Reading history is fine.

    yes   await run.step(implementing, request, commit="implement what the run was asked for")
    no    await run.verify("git add -A && git commit -m 'implement'")
    no    (in a prompt) When you are done, commit your changes.

## Commit messages

A commit is the `commit=` argument on the step that did the work. It is a few words saying what
the step did, and for looped work which round it was, so a reader can follow the branch without
the run record. A step with no `commit=` has its changes wiped, so every step that writes passes
one. A step whose role only reports passes none.

    yes   commit=f"fix what review round {round_number + 1} found"
    no    commit="fix what the review found"            (which round?)
    yes   review = await run.step(reviewing, request)
    no    review = await run.step(reviewing, request, commit="review")

## Restrictions

`Restriction` has four members: `NO_VCS_WRITES`, `NO_FILE_WRITES`, `NO_SHELL`, `NO_NETWORK`.
Give each role every one it can still do its job under.

- Every role gets `NO_VCS_WRITES`, because commits come from AGL and never from an agent.
- A role that only reports gets `NO_FILE_WRITES`. It has nothing to write.
- `NO_SHELL` unless the role has to run something, `NO_NETWORK` unless it has to reach the web.

    yes   restrictions={Restriction.NO_FILE_WRITES, Restriction.NO_VCS_WRITES,
                        Restriction.NO_SHELL, Restriction.NO_NETWORK},
    no    Role(name="implement", instructions=..., on_activity=watch)   (it can commit)

## Effort

Every model names its effort. A bare member runs at the tool's default, which nobody chose and
which can change without a word.

    yes   @role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), accepts=(str, Review))
    no    @role(model=Claude.OPUS, accepts=(str, Review))

## Files

- `__init__.py` is the workflow's shape and nothing else: `Parameters`, the roles bound once, the
  workflow function, and a helper only if it is itself part of the shape.
- `display.py` holds all display state and every screen.
- `roles.py` holds payloads, tools and role factories.
- `prompts/` has one markdown file per role.
- Imports between these are relative.
- `pyproject.toml` is exactly this, with the name and version filled in:

      [project]
      name = "<name>"
      version = "0.1.0"

      [project.entry-points."agl.workflows"]
      <name> = "<name>:<name>"

      [tool.agl]
      requires = "agents-gl>=<current agents-gl version>"

    no    Screen in __init__.py
    no    asking.py, a module of its own for one tool

## Bind roles at module level

Calling a factory checks its prompt against its `accepts=`. Call it at module level and
`agl workflows <name>` runs that check. Call it inside the workflow function and nothing checks
it until a run gets there, having already paid for every step before it.

    yes   implementing = implementer(watch=partial(report, "OPUS"))        (module level)
    no    async def workflow_builder(run):  ...  designing = designer(...)

## accepts=

At a step, `accepts=` is a permission: what the step may be handed. At the declaration it is a
demand: every accepted type must appear in the prompt as a placeholder, which is the type's
name between doubled braces, and no other placeholder may appear. (This file writes them as
`{{<Review>}}`, because a literal one here would be substituted.)

    yes   accepts=(str, Review), and implement.md places {{<str>}} and {{<Review>}}
    no    accepts=(str, Review), and the prompt places only {{<str>}}   (refused)

- Padded braces such as `{{ <Review> }}` are refused.
- Every occurrence is substituted, including one mentioned in passing in a sentence.
- Inputs arrive as canonical JSON. Say which fields the prompt reads.
- A type the step did not pass renders exactly `Not provided`. Say what that means for it.
- Two inputs of one type share one slot. A step that needs two strings declares a dataclass.
- Never pass a round counter as an input. AGL tells repeated calls apart by itself, and a
  counter only breaks replay. A varying `commit=` is fine, because it is not an input.

## The rest of what the SDK does not forgive

- `on_activity` only assigns. Format in the view, not in the callback.
- Reach the checkout only through `run.verify(command)`, never through `run.services`.
- A loop where agents answer each other has a cap and ends in `Stop`, saying what was left
  undone. A loop where a person answers every round has no cap, because the person is the cap.

    yes   raise Stop(f"{MAX_ROUNDS} review rounds and the last one still had findings:\n\n{findings}")
    no    return   (after the last round, with the findings still open)
