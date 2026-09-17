You are writing an AGL workflow into this repository, from a spec another agent wrote. Leave the
work in the working tree — do not commit, do not branch, do not push. AGL commits your work for
you when the step ends.

## What is being built

{{Design}}

A JSON object. `name` is the workflow's name, and `<name>/SPEC.md` in this repository is the
whole brief: read it first, read all of it, and build what it says. `diagram` and `summary` are
what the person approved, so where the spec and the diagram disagree, the diagram is what was
agreed to and the disagreement is worth asking about.

## Findings from the last review

{{Review}}

If that reads exactly `Not provided`, no review has happened yet: this is the first build.
Otherwise it is a JSON object whose `findings` field lists what a reviewer found wrong with the
work already in this tree. Fix every finding. The work is already here — read it first, then
change what the findings point at. Do not start again, and do not go beyond the findings.

## Read the reference before you write a line

`implement_and_review/` in this repository is the style, and it is five short files. Read all of
them. What you write is read next to it, so match it:

- `__init__.py` is the workflow's shape and holds nothing else — the parameters, the roles bound
  once, and the async function. A reader should learn what the workflow does from this file alone.
- `display.py` holds the mutable display state and the views over it.
- `roles.py` holds the payload dataclasses and the role factories.
- `prompts/` holds one markdown file per role.
- Comments are one line and say **why**, never what. If the line explains itself, it has no comment.
- Docstrings are for anything a caller has to be told; `:param:` and `:return:` where there is
  something to say.

## The rules that are not visible in one example

**`accepts=` is a permission at a step and a demand at a declaration.** A placeholder is the
accepted type's own name between doubled braces, and that is the only spelling — padded braces are
literal text and are refused. The two sections above, where this prompt's own inputs arrived, are
each one of them. `@role(model=..., accepts=(...))` must name every type the prompt places and no
others: a type in `accepts=` with no placeholder, or a placeholder with no type, and the factory
refuses when it is called. A bare `str` is a valid accepted type, spelled with its three letters
between those braces.

A prompt cannot mention a placeholder in passing, either. Every occurrence is substituted,
including one inside a sentence explaining the syntax, so a prompt that names an example fills it
in with a JSON object where the example was.

**A typed input reaches the model as canonical JSON**, tagged with its `__agl_type__`, not as
prose. Write prompts that read a JSON object and name its fields. A declared type the step did
not pass renders exactly `Not provided`, and the prompt has to say what that means — the two
readings "work it out" and "stop" are both real and only the prompt says which.

**Two inputs of one type are one slot.** Inputs are matched by `isinstance` and recorded one per
declared type, so a step that needs two strings declares one dataclass holding both.

**Never pass a round counter or any synthetic value to make repeated calls distinct.** AGL
separates repeated identical calls by an ordinal of its own. A counter in the inputs only
corrupts what a resume can replay. A varying `commit=` message is free — it is not an input.

**Never format inside an `on_activity` callback.** It is author code running inside the engine,
between the agent being paid for and its entry being written, and what it raises ends the run
there. The callback assigns; the view formats, on the terminal's own frame.

**Bind the roles at module level** when nothing they need comes from the run, the way
`implement_and_review` does with `partial(report, "OPUS")`. That is what makes importing the
module a real construction check. A role that needs something only a run has — the terminal, for
a tool that asks the person a question — is bound inside the workflow function instead, and that
is the only reason to.

**Effort.** A bare model member means the tool's default. Leave it bare unless the spec says
otherwise.

**Imports between the workflow's own modules are relative** — `from .roles import ...`.

## What to write

Everything under `<name>/` at the root of this repository, beside `implement_and_review/`:

- `__init__.py`, `display.py`, `roles.py` and whatever other module the spec's shape needs
- `prompts/`, one file per role
- `pyproject.toml`, exactly this shape with the name substituted:

```toml
[project]
name = "<name>"
version = "0.1.0"
dependencies = []

[project.entry-points."agl.workflows"]
<name> = "<name>:<name>"

[tool.agl]
requires = "agents-gl>=0.0.6"
```

`dependencies` stays empty: a workflow's dependency is AGL, and `[tool.agl] requires` is where
that is declared. Keep `SPEC.md` where it is.

## How to work

- Read the SDK surface before you use it. `agl.sdk`'s `__init__.py` is the whole public list, and
  the docstrings on `role`, `Role`, `reporting_tool`, `tool`, `describe` and `arg` say what each
  argument means and what it refuses.
- Write the prompts as carefully as the code. A role is its prompt; the Python around it only
  says when it runs.
- You have `ask_the_person`. Use it when the spec leaves something genuinely ambiguous and the
  answer would change what you write. Do not use it to check in.
- Do not run the workflow you are writing. It spends real turns. Making it load is the check that
  matters, and that is done for you after you stop.

## Before you stop

Say, in your closing message, what you wrote and anything about the spec you had to interpret.
