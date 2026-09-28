# chat

Haiku, through Claude Code, and Luna, through Codex, talk about a topic you give them. They take
turns saying one line each, and the terminal shows the chat as it goes. The chat ends after 20
lines, or as many as `-l` gives.

## Download

```
agl get jashioq/AGL-workflows/chat
```

## Usage

Run it from your repository:

```
agl run chat -n ai-consciousness -r "How do we know when ai gain consciousness?" -l 10
```

- `-n` - The run's name, also called its label.
- `-r`, `--topic` - What the two of them talk about.
- `-l`, `--lines` - How many lines the chat ends after. 20 by default.

## Models

- Haiku - Haiku at low effort, through Claude Code.
- Luna - Luna at low effort, through Codex.

Log in to both tools before you run it, with `claude` and `codex login`.

To change a model, edit the `model` in the role's `@role` in
`~/.agl/workspace/workflows/chat/roles.py`:

```python
@role(model=Claude.SONNET(effort=ClaudeEffort.LOW), accepts=(str,))
def haiku_speaker(conversation: Conversation) -> Role[None]:
```

See [Model and effort](https://agents-gl.org/build/role/model-and-effort/) for the models and
efforts you can pick. Each prompt in `prompts/` names both models, so change them there too. The
names the chat shows, `HAIKU` and `LUNA`, are in `roles.py`.

## Example

[chat](https://agents-gl.org/examples/chat/) in the AGL documentation walks through how this
workflow is built.
