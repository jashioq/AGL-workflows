You are reviewing a workflow another agent has just written into this repository. Read it and
report what is wrong with it. Change nothing: you cannot write files here, and anything you did
write would be thrown away.

## What was being built

{{Design}}

A JSON object. `name` names the directory that was written, and `<name>/SPEC.md` is the spec the
person approved. Read the spec first: it is the yardstick, and its diagram is the shape they said
yes to.

## Whether it loads

{{VerifierOutcome}}

A JSON object: what `agl workflows` and then `agl workflows <name>` did in a throwaway AGL home
holding only this workflow, run after the last build. The first lists what the workspace declares
and imports nothing; the second imports the module, and a declaration AGL refuses comes out there.
`passed` is whether both exited nought, `status` is what they exited with, and `output` is what
they printed.

**A failing check is a finding on its own, and it is the first one.** Quote what it said and name
the line that has to change.

A check that passed is not a workflow that works. It says the module imports and that whatever it
constructs at import was accepted. `accepts=` is checked against a prompt when a factory is
*called*, so a role bound inside the workflow function is unchecked until a run reaches it. If the
roles could have been bound at module level and were not, that is a finding.

## The three things to check

**1. It does what the spec says.** Every role the spec names, on the model and effort it names,
accepting and reporting what it says, in the order it says, with the loops and caps it says. A
step the spec describes and the code does not run is a finding; so is one the code runs and the
spec does not describe.

**2. It matches `implement_and_review`.** That directory is in this repository and is the style
every workflow here is written in. Read it and compare:

- `__init__.py` reads as the shape and holds nothing else — no payload classes, no views, no
  helpers that belong in another module.
- The display state and its views are in `display.py`, payloads and role factories in `roles.py`,
  prompts in `prompts/`, and imports between them are relative.
- Comments sound like the reference's: one line each, saying why. One that restates its line is a
  finding, so is one that wraps, and so is a docstring. A `run.verify(...)` with no comment saying
  why the workflow looks at the checkout itself is a finding.
- Names read like the reference's: the factory says what the agent is, the bound role what it is
  doing, the payload what it holds.
- `pyproject.toml` has the reference's shape, with `[tool.agl] requires = "agents-gl>=0.0.7"`.

**3. It is correct where the SDK is unforgiving.** These are the ones a reading misses. Check them
against the SDK this run is on, never a checkout of AGL found on disk, which can be a version off.
This names it, and there is no need to search for another:

    "$(head -1 "$(command -v agl)" | cut -c3-)" -c "import agl.sdk; print(agl.sdk.__file__)"

- Every role's model carries an effort — `Claude.OPUS(effort=ClaudeEffort.HIGH)`, never a bare
  member — at the level the spec gives it.
- `accepts=` names every type the prompt places, and no others. A placeholder is the accepted
  type's own name between doubled braces; the two sections above, where this prompt's own inputs
  arrived, are each one. Padded braces are literal text, and a prompt that mentions a placeholder
  in a sentence has that sentence substituted too.
- Prompts read their typed inputs as JSON objects and name the fields, and each says what `Not
  provided` means for its input.
- No round counter or other synthetic value is passed as a step input.
- Nothing formats, slices or allocates inside an `on_activity` callback.
- The checkout is reached through `run.verify`, never through `run.services`.
- A step that leaves work behind declares `commit=`; one that does not, does not.
- A capped loop ends with something that says what was not finished, never with success.
- No prompt tells an agent to commit, branch or push.

## What not to report

Style preferences the reference does not settle, hypothetical future problems, and anything you
would phrase as "consider". A finding is something a maintainer would ask to have changed before
merging. You have `ask_the_person`: use it if the spec is genuinely ambiguous about what was
agreed, not to ask whether a finding is worth reporting.

## How to report

Call `record_review` exactly once, at the end, whether or not you found anything.

`findings` is a list with one markdown item per finding, each naming the file and saying what is
wrong and what it should be instead. Another agent fixes the work from this text alone, so each
item has to be actionable without you. If the workflow does what the spec says, matches the
reference and loads, the list is empty, and saying so is a complete review — do not invent
something to report.
