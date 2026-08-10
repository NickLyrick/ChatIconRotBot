"""Build Telegram rich messages that carry native tables.

Telegram has carried table blocks since Bot API 10.1, so the rows are handed
over as data and drawn by the client. That replaces rendering them to a PNG
through pandas, WeasyPrint, poppler and Pillow: the result is selectable and
searchable, and the bot needs no native libraries at all.
"""

from collections.abc import Iterable, Sequence
from typing import Any

from aiogram.types import (
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    InputRichBlockUnion,
    InputRichMessage,
    RichBlockTableCell,
)

# Numeric columns read better flush right; everything else stays left.
RIGHT_ALIGNED_COLUMNS = frozenset({"Trophies", "Score"})

# Header of the row-number column, matching the 1-based index of the old tables.
ROW_NUMBER_HEADER = "#"


def _cell(value: Any, align: str, is_header: bool = False) -> RichBlockTableCell:
    """Wrap a single value into a table cell."""

    return RichBlockTableCell(
        align=align,
        valign="middle",
        text=str(value),
        # Passing False would still mark the cell, so send nothing instead.
        is_header=True if is_header else None,
    )


def table_block(
    data: Iterable[Sequence[Any]],
    columns: Sequence[str],
    caption: str | None = None,
) -> InputRichBlockTable:
    """Lay the rows out as one table block.

    The first column numbers the rows, the way the rendered tables did through
    the DataFrame index.
    """

    alignments = [
        "right" if column in RIGHT_ALIGNED_COLUMNS else "left" for column in columns
    ]

    header = [_cell(ROW_NUMBER_HEADER, "right", is_header=True)]
    header += [
        _cell(column, alignment, is_header=True)
        for column, alignment in zip(columns, alignments)
    ]

    rows = []
    for number, row in enumerate(data, start=1):
        cells = [_cell(number, "right")]
        cells += [_cell(value, alignment) for value, alignment in zip(row, alignments)]
        rows.append(cells)

    return InputRichBlockTable(
        cells=[header, *rows],
        is_bordered=True,
        is_striped=True,
        caption=caption,
    )


def heading_block(text: str, size: int = 3) -> InputRichBlockSectionHeading:
    """A section heading, used to title a message holding several tables."""

    return InputRichBlockSectionHeading(text=text, size=size)


def rich_message(blocks: Sequence[InputRichBlockUnion]) -> InputRichMessage:
    """Wrap blocks into a message ready for sendRichMessage."""

    return InputRichMessage(blocks=list(blocks))


def table_message(
    data: Iterable[Sequence[Any]],
    columns: Sequence[str],
    caption: str | None = None,
) -> InputRichMessage:
    """Shorthand for a message holding a single table."""

    return rich_message([table_block(data, columns, caption)])
