from typing import Final

from agl.sdk import Terminal, Tool, ToolResult, tool

from .display import question
from .roles import Asked

ASK: Final = "ask_the_person"

_DESCRIPTION: Final = (
    "Ask the person running this workflow a question, and wait for their answer. Use it when the "
    "decision is genuinely theirs - which of two shapes to build, whether a name is right, what a "
    "vague request meant - rather than guessing. It is not for anything you could settle by "
    "reading the repository. Each call is one question and returns one answer, and you may call it "
    "as often as you need."
)

NO_QUESTION: Final = (
    "That call asked nothing: `question` was blank. A question is the whole of what the person "
    "sees, so write what you are asking in full and call this tool again."
)

SAID_NOTHING: Final = (
    "The person answered with nothing at all. Take that as no preference either way, use your own "
    "judgement, and carry on."
)


def asking(terminal: Terminal) -> Tool:
    """Build the tool a role asks its question through, which is the whole of how a role asks one.

    A question is an ordinary tool. It goes in `tools` beside the role's reporting tool, the model
    calls it by name, and this handler waits on the terminal for the answer before returning. There
    is no callback on `Role` for this and there was one once: it was taken off deliberately.

    :param terminal: the run's own, so the question queues in front of the board rather than over it
    :return: a tool to put on a role; the same object may go on every role that offers one
    """

    async def answered(asked: Asked) -> ToolResult:
        if not asked.question.strip():
            return ToolResult(text=NO_QUESTION, rejected=True)
        answer = await terminal.show(question, asked=asked)
        return ToolResult(text=answer or SAID_NOTHING)

    return tool(ASK, _DESCRIPTION, Asked, answered)
