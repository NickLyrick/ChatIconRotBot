"""Parse and format the avatar rotation settings that chat admins type.

Admins enter and read dates in Moscow time; the database stores them in UTC.
"""

from datetime import datetime, timedelta, timezone

import pytz

CHAT_TIMEZONE = pytz.timezone("Europe/Moscow")
INPUT_FORMAT = "%d/%m/%Y %H:%M"
DISPLAY_FORMAT = "%d.%m.%Y %H:%M"

# Upper bound for the interval: keeps the scheduler's date arithmetic in range.
MAX_DELTA_DAYS = 365


def parse_rotation_date(text: str) -> datetime:
    """Parse ``DD/MM/YYYY HH:MM`` in Moscow time into an aware UTC datetime.

    Raises ValueError when the text does not match the format.
    """

    naive = datetime.strptime(text.strip(), INPUT_FORMAT)
    return CHAT_TIMEZONE.localize(naive).astimezone(timezone.utc)


def format_chat_date(value: datetime) -> str:
    """Format a stored date for the chat, in Moscow time."""

    return value.astimezone(CHAT_TIMEZONE).strftime(DISPLAY_FORMAT)


def example_rotation_date(now: datetime) -> str:
    """A valid /set_date argument for tomorrow at 18:00, Moscow time."""

    tomorrow = now.astimezone(CHAT_TIMEZONE) + timedelta(days=1)
    return tomorrow.replace(hour=18, minute=0).strftime(INPUT_FORMAT)


def parse_delta(text: str | None) -> int | None:
    """Return the interval in days, or None unless it is a whole number in range."""

    if text is None:
        return None
    try:
        delta = int(text.strip())
    except ValueError:
        return None
    return delta if 1 <= delta <= MAX_DELTA_DAYS else None
