You are writing an AGL workflow into this repository, from the spec below. Another agent reviews
it against that spec and against the guidelines that follow this prompt.

## The spec

{{Spec}}

It is a JSON object, and it is the whole of your brief:

- `name` is the directory to write, at the root of this repository.
- `does` says what the workflow does.
- `shape` is its diagram, then each step in order.
- `roles` gives each role's model, effort and restrictions.
- `decisions` is what the person decided along the way.

If it reads `Not provided`, stop at once and write nothing.

Build exactly what it says. Where it is silent, choose the reading a careful colleague would, and
say which one in your closing message.

## Findings from the last review

{{Review}}

If that reads `Not provided`, this is the first build. Otherwise it is a JSON object, and its
`findings` list what the reviewer found wrong with the work already here. Read that work, fix
every finding, and change nothing else.

## How to work

- Write `<name>/` with `__init__.py`, `display.py`, `roles.py`, `prompts/` and `pyproject.toml`,
  as the guidelines lay out.
- Read the SDK before you use it. Its path is at the end. The docstrings on `role`, `Role`,
  `reporting_tool`, `tool`, `describe` and `arg` say what each argument means and what it
  refuses.
- Write each prompt as carefully as the code: a role is its prompt.
- Write no comments and no docstrings.
