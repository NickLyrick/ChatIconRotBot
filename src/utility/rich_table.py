"""Build Telegram rich messages that carry a native table.

The alternative is :func:`src.utility.tools.table`, which renders the same rows
to a PNG through pandas, WeasyPrint, poppler and Pillow. Telegram has carried
table blocks since Bot API 10.1, so the rows can be handed over as data and
rendered by the client instead — selectable, searchable and free of the whole
image pipeline.
"""

from collections.abc import Iterable, Sequence
from typing import Any

from aiogram.types import InputRichBlockTable, InputRichMessage, RichBlockTableCell

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


def table_message(
    data: Iterable[Sequence[Any]],
    columns: Sequence[str],
    caption: str | None = None,
) -> InputRichMessage:
    """Lay the rows out as a rich message holding one table.

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
        cells += [
            _cell(value, alignment) for value, alignment in zip(row, alignments)
        ]
        rows.append(cells)

    return InputRichMessage(
        blocks=[
            InputRichBlockTable(
                cells=[header, *rows],
                is_bordered=True,
                is_striped=True,
                caption=caption,
            )
        ]
    )
