import shutil
import textwrap
from typing import Final
from agl.sdk import Row, Rows, Screen, Terminal

# The adapter sizes a row by its characters, escapes included, so these are as short as the
# colours allow: 256 for an orange there is no short code for, and truecolor would spend 19
ORANGE: Final = "\x1b[38;5;173m"
BLUE: Final = "\x1b[94m"
RESET: Final = "\x1b[0m"

PADDING: Final = [Row("")] * 3

spoken: list[tuple[str, str, str]] = []


async def opened(terminal: Terminal, header: str) -> None:
    await terminal.show(board, header=header)


def said(colour: str, name: str, message: str) -> None:
    spoken.append((colour, name, message))


def board(*, header: str) -> Screen:
    width, height = shutil.get_terminal_size()
    # A blank row ahead of every line but the first, so one turn is easy to tell from the next
    drawn = [row for line in spoken for row in (Row(""), *_rows(*line, width))][1:]
    # A board taller than the terminal has its last rows cropped away, and the last row is the
    # line that just landed - so the older end of the chat is what goes, and it scrolls nowhere
    room = max(height - len(PADDING) - 1, 1)
    return Screen(Rows([Row(header), *PADDING, *drawn[-room:]]))


def _rows(colour: str, name: str, message: str, width: int) -> list[Row]:
    # One cell a row, and the escapes around the name are counted as columns of it: both come off
    # what a line may hold, so the wrapping is done here where the rows it adds are still counted
    room = max(width - len(colour) - len(RESET) - len(name) - 2, 1)
    wrapped = textwrap.wrap(message, room) or [""]
    under = " " * (len(name) + 2)
    return [Row(f"{colour}{name}:{RESET} {wrapped[0]}"), *(Row(under + on) for on in wrapped[1:])]
