"""Parse and format the avatar rotation settings that chat admins type.

Admins enter and read dates in Moscow time; the database stores them in UTC.
"""

from datetime import date, datetime, time, timedelta, timezone

import pytz

CHAT_TIMEZONE = pytz.timezone("Europe/Moscow")
INPUT_FORMAT = "%d/%m/%Y %H:%M"
DISPLAY_FORMAT = "%d.%m.%Y %H:%M"

# Upper bound for the interval: keeps the scheduler's date arithmetic in range.
MAX_DELTA_DAYS = 365

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def chat_today(now: datetime) -> date:
    """Today's date in Moscow."""

    return now.astimezone(CHAT_TIMEZONE).date()


def rotation_at(day: date, hour: int) -> datetime:
    """The UTC moment of ``hour``:00 Moscow time on ``day``."""

    naive = datetime.combine(day, time(hour=hour))
    return CHAT_TIMEZONE.localize(naive).astimezone(timezone.utc)


def available_hours(day: date, now: datetime) -> list[int]:
    """Hours of ``day`` (Moscow time) that are still in the future."""

    return [hour for hour in range(24) if rotation_at(day, hour) > now]


def upcoming_days(now: datetime, count: int = 7) -> list[date]:
    """The next ``count`` days, starting today, that still have a free hour."""

    today = chat_today(now)
    days = [today + timedelta(days=offset) for offset in range(count + 1)]
    return [day for day in days if available_hours(day, now)][:count]


def with_hour(current: datetime, hour: int, now: datetime) -> datetime:
    """Move the next rotation to ``hour``:00, keeping its day when possible.

    An overdue rotation moves to today; when the hour has already passed that
    day, the rotation moves to the next day.
    """

    day = max(current.astimezone(CHAT_TIMEZONE).date(), chat_today(now))
    moved = rotation_at(day, hour)
    return moved if moved > now else rotation_at(day + timedelta(days=1), hour)


def day_label(day: date, now: datetime) -> str:
    """A short button label: «Сегодня», «Завтра» or «Пт 13.11»."""

    offset = (day - chat_today(now)).days
    if offset == 0:
        return "Сегодня"
    if offset == 1:
        return "Завтра"
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"


def describe_settings(next_rotation: datetime, delta: int) -> str:
    """The chat's schedule as shown to admins."""

    return (
        f"Ближайшая дата смены: {format_chat_date(next_rotation)} (МСК).\n"
        f"Промежуток между сменами: {delta}д."
    )


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
