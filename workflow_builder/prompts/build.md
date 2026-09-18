You are writing an AGL workflow into this repository, from a spec another agent wrote. Leave the
work in the working tree — do not commit, do not branch, do not push. AGL commits your work for
you when the step ends.

## What is being built

{{Design}}

A JSON object. `name` is the workflow's name, and `<name>/SPEC.md` in this repository is the
whole brief: read all of it first, and build what it says. `diagram` and `summary` are what the
person approved, so where the spec and the diagram disagree, the diagram is what was agreed and
the disagreement is worth asking about.

## Findings from the last review

{{Review}}

If that reads exactly `Not provided`, this is the first build. Otherwise it is a JSON object whose
`findings` field lists what a reviewer found wrong with the work already in this tree. Fix every
finding: read the work first, then change what the findings point at. Do not start again, and do
not go beyond the findings.

## Write it like the reference

`implement_and_review/` in this repository is the style, and it is five short files. Read all of
them before you write a line. What you write is read beside it, so match it:

- `__init__.py` is the workflow's shape and nothing else — the parameters, the roles bound once,
  and the async function. A reader learns what the workflow does from this file alone.
- `display.py` holds the mutable display state and the views over it, `roles.py` the payload
  dataclasses and the role factories, and `prompts/` one markdown file per role.
- Imports between the workflow's own modules are relative.

**Comments.** Read the ones in `implement_and_review/__init__.py` first: that is the voice. One
line each, never wrapped, and each says why — a comment that restates its line is deleted, not
shortened. No docstrings. Say why wherever the shape does something a reader would ask about: a
cap, the way a loop ends, a step that does not commit. One line always has a comment: any
`run.verify(...)`, or anything else that reaches the checkout itself rather than through an
agent's step. Say why the workflow looks there.

## The rules the reference does not show

**Every role names its effort**, at the model and level the spec gives it:
`@role(model=Claude.OPUS(effort=ClaudeEffort.HIGH), ...)`. A bare `Claude.OPUS` runs at the tool's
own default, which is silent and can change. `ClaudeEffort` is exported from `agl.sdk`.

**`accepts=` names exactly the types the prompt places.** A placeholder is the accepted type's own
name between doubled braces, and that is the only spelling — padded braces are literal text and
are refused. The two sections above, where this prompt's own inputs arrived, are each one. A type
in `accepts=` with no placeholder, or a placeholder with no type, and the factory refuses when it
is called. A bare `str` is a valid type, spelled with its three letters between the braces. A
prompt cannot mention a placeholder in passing either: every occurrence is substituted, including
one in a sentence explaining the syntax.

**A typed input reaches the model as canonical JSON**, tagged with its `__agl_type__`. Write
prompts that read a JSON object and name its fields. A declared type the step did not pass renders
exactly `Not provided`, and each prompt says what that means for its input — "work it out" and
"stop" are both real readings, and only the prompt says which.

**Two inputs of one type are one slot.** Inputs are matched by `isinstance` and recorded one per
type, so a step that needs two strings declares one dataclass holding both.

**Never pass a round counter** or any synthetic value to tell repeated calls apart. AGL separates
them with an ordinal of its own, and a counter in the inputs only corrupts what a resume can
replay. A varying `commit=` message is free — it is not an input.

**Never format inside an `on_activity` callback.** It runs inside the engine, between the agent
being paid for and its entry being written, and what it raises ends the run there. The callback
assigns; the view formats.

**Bind the roles at module level**, as the reference does. That is what makes importing the module
a real check of each prompt against its `accepts=`. Only a role that needs something a run has —
the terminal, for a tool that asks the person — is bound inside the workflow function.

**Reach the checkout only through `run.verify(command)`**, which runs a shell command in this
run's own checkout and returns `passed`, `status` and `output`. Never open a workspace through
`run.services`: that hands back the root run's checkout, not necessarily this one.

## What to write

Everything under `<name>/` at the root of this repository, beside `implement_and_review/`: the
three modules and any other the spec's shape needs, `prompts/` with one file per role, and
`pyproject.toml` in exactly this shape, the name substituted:

```toml
[project]
name = "<name>"
version = "0.1.0"

[project.entry-points."agl.workflows"]
<name> = "<name>:<name>"

[tool.agl]
requires = "agents-gl>=0.0.7"
```

Keep `SPEC.md` where it is.

## How to work

- Read the SDK before you use it: the one this run is on, never a checkout of AGL found on disk,
  which can be a version off. This names it:

      "$(head -1 "$(command -v agl)" | cut -c3-)" -c "import agl.sdk; print(agl.sdk.__file__)"

  Its `__init__.py` is the whole public list, and the docstrings on `role`, `Role`,
  `reporting_tool`, `tool`, `describe` and `arg` say what each argument means and what it refuses.
- Write the prompts as carefully as the code. A role is its prompt; the Python only says when it
  runs.
- You have `ask_the_person`. Use it when the spec leaves something genuinely ambiguous and the
  answer would change what you write. Do not use it to check in.
- Do not run the workflow you are writing: it spends real turns. Whether it loads is checked for
  you after you stop.

## Before you stop

Say, in your closing message, what you wrote and anything in the spec you had to interpret.
