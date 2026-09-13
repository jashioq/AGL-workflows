# ralph

One prompt, one fresh agent, over and over, until an external command says it is done.

The technique is **Geoffrey Huntley's** — [ghuntley.com/ralph](https://ghuntley.com/ralph). The
whole of it is that nothing is remembered: the same prompt goes to a brand new agent each time
round, so work can only accumulate on disk and in git history, and an agent can only learn what
its predecessors did by reading the repository. And what decides the loop is over is a build, a
test suite, a gate — something outside the agent that exits nought or does not — never the agent
saying it is finished. The prompts here are this workflow's own; the idea is his.

```
agl run ralph -n percentile -r "add a percentile function with tests" --gate "pytest -q"
```

## What happens

Each iteration:

1. **The agent works.** A fresh agent is given the request, the gate command, and — from the
   second iteration on — the exit status and output of the last gate run. It reads the
   repository and `RALPH.md`, takes the next thing, does it, and leaves the work in the tree.
   AGL commits it as `ralph iteration N`.
2. **The gate runs.** The command from `--gate` runs in that same checkout, through a shell, with
   the commit in place.
3. **Exit 0 ends the run.** Anything else and the status and output go into the next iteration as
   a typed input, and round again.

Reaching `--max-iterations` with the gate still failing ends the run with a `Stop` saying so, the
last failure attached. It never reports success.

## Parameters

| flag | | |
| --- | --- | --- |
| `-r`, `--request` | required | what you want built, in a sentence or two |
| `-g`, `--gate` | required | the command that decides done; exit 0 ends the run |
| `-m`, `--max-iterations` | default 10 | how many rounds to pay for before giving up |

The gate is run through a shell in the run's checkout, so operators work: `pytest -q`,
`make test`, `npm run build && npm test`. It is run by AGL rather than by the agent — the agent
is told what the command is and asked to run it too, but its opinion of the result is not what
ends the loop.

**Ten iterations**, and that is a cost decision rather than a technical one. Huntley's loop has
no cap; it runs until the gate goes green or a person stops it. A workflow spending real money
needs an end it reaches on its own, and ten is set where a converging run has room and a stuck
one is not left to discover it fifty times. Three — what a review loop uses — is too few here:
the first iteration usually goes on reading the repository and writing the plan.

## RALPH.md

The plan lives in `RALPH.md` at the root of the repository being worked on, and **the agent
creates it**, on the first iteration, not the workflow. That is forced rather than chosen: AGL
resets the checkout to the chain's head immediately before dispatching each agent, so anything
the workflow wrote into the tree beforehand is gone before the first agent sees it. The prompt
asks each iteration to read it first, take the topmost undone item, and rewrite it before
stopping — what it finished, what it learned, and what the next one should do.

It is committed along with everything else, onto the run's own branch (`agl/<label>`) and never
onto yours, so `git log` on that branch is the loop's history and `RALPH.md` in that tree is
where the last iteration thought it had got to.

## What the agent may not do

The role runs with `NO_VCS_WRITES`. Reads are untouched — `git log` and `git show` are the memory
and are worth using — but the run's branch is the only copy of what earlier iterations did, and
an agent free to reset, amend or rebase can throw away the thing the loop is built on. AGL
records each iteration itself.

## The display

Two lines, updating in place:

```
ralph  04:12
OPUS   writing tests for the percentile helper               01:03
```

The run's name and its clock; then whoever is working — the agent, or the gate while the gate is
running — what it last said it was doing, and how long it has been at it.
