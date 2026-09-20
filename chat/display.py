import shutil
import textwrap
from time import monotonic
from typing import Final
from agl.sdk import Row, Rows, Screen, Terminal

# One cube colour each, built from the same three channel levels so neither outshines the other,
# and 11 characters against the 19 a truecolor span would spend - the adapter sizes a row by its
# characters, escapes included
ORANGE: Final = "\x1b[38;5;209m"
BLUE: Final = "\x1b[38;5;69m"
RESET: Final = "\x1b[0m"

PADDING: Final = [Row("")] * 3
INDENT: Final = " " * 10

# The braille spinner running backwards, a frame every tenth of a second - which is the rate the
# board redraws at, so each of the eight is drawn once and the spin comes out even
SPINNER: Final = "⣷⣯⣟⡿⢿⣻⣽⣾"
FRAME: Final = 0.1

spoken: list[tuple[str, str, str]] = []
thinking: list[tuple[str, str]] = []


async def opened(terminal: Terminal, header: str) -> None:
    await terminal.show(board, header=header)


def said(colour: str, name: str, message: str) -> None:
    spoken.append((colour, name, message))


def waiting(colour: str, name: str) -> None:
    thinking[:] = [(colour, name)]


def quiet() -> None:
    thinking.clear()


def board(*, header: str) -> Screen:
    width, height = shutil.get_terminal_size()
    blocks = [_rows(*line, width) for line in spoken] + [_spinning()]
    # A blank row ahead of every block but the first, so one turn is easy to tell from the next
    drawn = [row for block in blocks if block for row in (Row(""), *block)][1:]
    # A board taller than the terminal has its last rows cropped away, and the last row is the
    # line that just landed - so the older end of the chat is what goes, and it scrolls nowhere
    room = max(height - len(PADDING) - 1, 1)
    return Screen(Rows([Row(header), *PADDING, *drawn[-room:]]))


def _rows(colour: str, name: str, message: str, width: int) -> list[Row]:
    # The escapes are counted as columns of the row carrying them, so they come off what the
    # first line may hold - and off the rest too, which is what keeps the right edge even
    room = max(width - len(INDENT) - len(colour) - len(RESET), 1)
    wrapped = textwrap.wrap(message, room) or [""]
    return [Row(_head(colour, name) + wrapped[0]), *(Row(INDENT + on) for on in wrapped[1:])]


# Padded on the visible name and not on the escapes around it, so both names, and the spinner
# standing in for a line that has not arrived, start their text in the same column
def _head(colour: str, name: str) -> str:
    return f"{colour}{name}:{RESET}" + " " * max(len(INDENT) - len(name) - 1, 1)


def _spinning() -> list[Row]:
    if not thinking:
        return []
    colour, name = thinking[0]
    # Read off the clock rather than counted, because a tally here would turn at whatever rate
    # the board happens to redraw at rather than at the one the frames were chosen for
    return [Row(_head(colour, name) + SPINNER[int(monotonic() / FRAME) % len(SPINNER)])]
