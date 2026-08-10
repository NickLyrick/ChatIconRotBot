"""Tests for :mod:`src.utility.rich_table`.

The rendering itself belongs to the Telegram client, so what is worth checking
is the shape handed to the API: the header row, the row numbering that the
image tables got from the DataFrame index, and the alignment of numeric
columns.
"""

from src.utility.rich_table import (
    ROW_NUMBER_HEADER,
    heading_block,
    rich_message,
    table_block,
    table_message,
)

TOP_ROWS = [("nick1", 12), ("nick2", 7)]
TOP_COLUMNS = ["Nickname", "Trophies"]


def get_table(message):
    """Return the single table block of a rich message."""

    assert len(message.blocks) == 1, "expected exactly one block"
    block = message.blocks[0]
    assert block.type == "table"
    return block


def test_header_row_is_marked_and_labelled():
    """The first row holds the column names and is flagged as a header."""

    table = get_table(table_message(TOP_ROWS, TOP_COLUMNS))

    header = table.cells[0]
    assert [cell.text for cell in header] == [ROW_NUMBER_HEADER, "Nickname", "Trophies"]
    assert all(cell.is_header for cell in header)


def test_rows_are_numbered_from_one():
    """The leading column reproduces the 1-based index of the rendered tables."""

    table = get_table(table_message(TOP_ROWS, TOP_COLUMNS))

    body = table.cells[1:]
    assert len(body) == len(TOP_ROWS)
    assert [row[0].text for row in body] == ["1", "2"]
    assert [row[1].text for row in body] == ["nick1", "nick2"]
    # Values are stringified — the API rejects a bare int in a cell.
    assert [row[2].text for row in body] == ["12", "7"]


def test_body_cells_are_not_headers():
    """Only the first row may carry is_header, otherwise every row looks bold."""

    table = get_table(table_message(TOP_ROWS, TOP_COLUMNS))

    for row in table.cells[1:]:
        assert all(cell.is_header is None for cell in row)


def test_numeric_columns_are_right_aligned():
    """Trophies is numeric, Nickname is not."""

    table = get_table(table_message(TOP_ROWS, TOP_COLUMNS))

    for row in table.cells:
        number, nickname, trophies = row
        assert number.align == "right"
        assert nickname.align == "left"
        assert trophies.align == "right"


def test_caption_is_carried_through():
    """The caption replaces the one the media group used to hold."""

    table = get_table(table_message(TOP_ROWS, TOP_COLUMNS, caption="Топ за всё время"))

    assert table.caption == "Топ за всё время"


def test_empty_data_still_yields_a_header():
    """An empty table must not raise; the handlers guard against sending it."""

    table = get_table(table_message([], TOP_COLUMNS))

    assert len(table.cells) == 1


def test_survey_results_fit_one_message():
    """finish_survey sends a heading followed by one table per category.

    The three categories used to travel as a media group of three images; they
    now have to reach the chat as a single message so that pinning it pins all
    of them.
    """

    categories = ["Игра", "Картинка", "Сложность"]
    message = rich_message(
        [
            heading_block("Результаты опроса за 07.2026"),
            *(
                table_block(
                    [("nick1", "Bloodborne", 9.5)],
                    columns=["Hunter", "Game", "Score"],
                    caption=f"Результаты в категории {category}",
                )
                for category in categories
            ),
        ]
    )

    assert [block.type for block in message.blocks] == ["heading", "table", "table", "table"]
    assert message.blocks[0].text == "Результаты опроса за 07.2026"
    assert [block.caption for block in message.blocks[1:]] == [
        f"Результаты в категории {category}" for category in categories
    ]


def test_message_is_serialisable_for_the_api():
    """The whole message must survive the dump aiogram sends over the wire."""

    message = table_message(TOP_ROWS, TOP_COLUMNS, caption="Топ")

    dumped = message.model_dump(exclude_none=True)
    assert set(dumped) == {"blocks"}, "only blocks may be set, not html or markdown"
    table = dumped["blocks"][0]
    assert table["type"] == "table"
    assert table["is_bordered"] is True
    assert len(table["cells"]) == len(TOP_ROWS) + 1
