# implement_and_review

Claude Code makes the change you ask for, and Codex reviews it. Claude Code fixes what each review
finds, for up to three reviews. A clean review finishes the run with the work committed on
`agl/<label>`, and a third review that still has findings stops it.

## Download

```
agl get jashioq/AGL-workflows/implement_and_review
```

## Usage

Run it from your repository:

```
agl run implement_and_review -n health-check -r "Add a health check endpoint"
```

- `-n` - The run's name, also called its label. The work ends up on the branch `agl/<label>`.
- `-r`, `--request` - What you want done.

Either agent can stop to ask you a question in the terminal. Pick one of its answers or type your
own.

## Models

- Implementer - Opus at medium effort, through Claude Code.
- Reviewer - Sol at medium effort, through Codex.

Log in to both tools before you run it, with `claude` and `codex login`.

To change a model, edit the `model` in the role's `@role` in
`~/.agl/workspace/workflows/implement_and_review/roles.py`:

```python
@role(model=Claude.SONNET(effort=ClaudeEffort.MEDIUM), accepts=(str, Review))
def implementer(watch: ActivityReporter) -> Role[None]:
```

See [Model and effort](https://agents-gl.org/build/role/model-and-effort/) for the models and
efforts you can pick. The names the terminal shows for each agent, `"OPUS"` and `"SOL"`, are in
`__init__.py`.

## Example

[implement_and_review](https://agents-gl.org/examples/implement_and_review/) in the AGL
documentation walks through how this workflow is built.
