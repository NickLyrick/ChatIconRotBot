"""Tests for :mod:`src.utility.schedule`: parsing and formatting chat settings."""

from datetime import datetime, timedelta, timezone

import pytest

from src.scheduler.runner import next_rotation_date
from src.utility.schedule import (
    MAX_DELTA_DAYS,
    example_rotation_date,
    format_chat_date,
    parse_delta,
    parse_rotation_date,
)

UTC = timezone.utc


# --- parse_rotation_date -------------------------------------------------------


def test_date_is_read_as_moscow_time_and_stored_in_utc():
    parsed = parse_rotation_date("31/12/2026 18:00")

    assert parsed == datetime(2026, 12, 31, 15, 0, tzinfo=UTC)
    assert parsed.utcoffset() == timedelta(0)


def test_surrounding_spaces_are_ignored():
    assert parse_rotation_date("  01/02/2027 00:30 ") == datetime(
        2027, 1, 31, 21, 30, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "text",
    ["", "31.12.2026 18:00", "31/12/2026", "2026/12/31 18:00", "32/12/2026 18:00", "31/12/2026 25:00"],
)
def test_malformed_date_is_rejected(text):
    with pytest.raises(ValueError):
        parse_rotation_date(text)


# --- format_chat_date / example_rotation_date ---------------------------------


def test_stored_date_is_shown_in_moscow_time():
    assert format_chat_date(datetime(2026, 12, 31, 15, 0, tzinfo=UTC)) == "31.12.2026 18:00"


def test_parse_and_format_round_trip():
    assert format_chat_date(parse_rotation_date("05/03/2027 09:15")) == "05.03.2027 09:15"


def test_example_date_is_valid_and_in_the_future():
    now = datetime(2026, 12, 31, 22, 0, tzinfo=UTC)  # already 1 January in Moscow

    example = example_rotation_date(now)

    assert example == "02/01/2027 18:00"
    assert parse_rotation_date(example) > now


# --- parse_delta --------------------------------------------------------------


@pytest.mark.parametrize("text, expected", [("1", 1), (" 7 ", 7), (str(MAX_DELTA_DAYS), MAX_DELTA_DAYS)])
def test_valid_delta(text, expected):
    assert parse_delta(text) == expected


@pytest.mark.parametrize(
    "text", [None, "", "0", "-3", "3.5", "три", str(MAX_DELTA_DAYS + 1), "10000000000"]
)
def test_invalid_delta(text):
    assert parse_delta(text) is None


def test_largest_delta_keeps_the_scheduler_in_range():
    """A rotation set far ahead with the largest interval must not overflow."""

    scheduled = datetime(9998, 1, 1, tzinfo=UTC)

    assert next_rotation_date(scheduled, MAX_DELTA_DAYS, scheduled) == scheduled + timedelta(
        days=MAX_DELTA_DAYS
    )
