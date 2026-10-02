# in_stages

Sonnet splits what you ask for into stages, then builds them one at a time. Each stage is
committed on `agl/<label>` when it is done, and the terminal shows every stage with its status and
its timer. It is made to show `agl resume`: stop the run part-way and resume it, and the stages
already done are not built again.

## Download

```
agl get jashioq/AGL-workflows/in_stages
```

## Usage

Run it from your repository:

```
agl run in_stages -n todo-app -r "Build a todo app for the command line" -s 5
```

- `-n` - The run's name, also called its label. The work ends up on the branch `agl/<label>`.
- `-r`, `--request` - What you want built.
- `-s`, `--stages` - How many stages to split it into.

Neither agent asks you anything.

## Resume

Stop the run with Ctrl+C while a stage is in progress, then continue it:

```
agl resume todo-app
```

The split and every finished stage come back from the run's record without an agent being started,
so they show `DONE 0:00`. The stage that was cut short starts again from the last finished one.

## Models

- Both agents - Sonnet at medium effort, through Claude Code.

Log in before you run it, with `claude`.

To change a model, edit the `model` in the role's `@role` in
`~/.agl/workspace/workflows/in_stages/roles.py`:

```python
@role(model=Claude.OPUS(effort=ClaudeEffort.MEDIUM), accepts=(str, Plan, Stage))
def worker() -> Role[None]:
```

See [Model and effort](https://agents-gl.org/build/role/model-and-effort/) for the models and
efforts you can pick. The name the terminal shows in front of each stage, `Sonnet`, is in
`display.py`.
