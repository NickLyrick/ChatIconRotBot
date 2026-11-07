"""Parse and format the avatar rotation settings that chat admins type.

Admins enter and read dates in their chat's time zone (Moscow by default); the
database stores them in UTC. Zones are IANA names such as ``Europe/Moscow``.
"""

from datetime import date, datetime, time, timedelta, timezone

import pytz

DEFAULT_TIMEZONE = "Europe/Moscow"
INPUT_FORMAT = "%d/%m/%Y %H:%M"
DISPLAY_FORMAT = "%d.%m.%Y %H:%M"

# Upper bound for the interval: keeps the scheduler's date arithmetic in range.
MAX_DELTA_DAYS = 365

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")

# Zones offered in the settings menu; any other IANA zone can be set by name.
TIMEZONE_CHOICES = {
    "Europe/Kaliningrad": "Калининград",
    "Europe/Moscow": "Москва",
    "Europe/Samara": "Самара",
    "Asia/Yekaterinburg": "Екатеринбург",
    "Asia/Omsk": "Омск",
    "Asia/Novosibirsk": "Новосибирск",
    "Asia/Krasnoyarsk": "Красноярск",
    "Asia/Irkutsk": "Иркутск",
    "Asia/Yakutsk": "Якутск",
    "Asia/Vladivostok": "Владивосток",
    "Asia/Magadan": "Магадан",
    "Asia/Kamchatka": "Камчатка",
    "Europe/Minsk": "Минск",
    "Europe/Kyiv": "Киев",
    "Asia/Almaty": "Алматы",
    "Asia/Tashkent": "Ташкент",
    "Asia/Tbilisi": "Тбилиси",
    "Asia/Yerevan": "Ереван",
    "Europe/Berlin": "Берлин",
    "Europe/London": "Лондон",
    "UTC": "UTC",
}

_ZONES_BY_KEY = {name.casefold(): name for name in pytz.all_timezones}
_ZONES_BY_KEY.update({label.casefold(): name for name, label in TIMEZONE_CHOICES.items()})


# --- zones --------------------------------------------------------------------


def get_zone(name: str | None) -> pytz.BaseTzInfo:
    """The zone with this IANA name; the default zone for a missing or unknown name."""

    try:
        return pytz.timezone(name or DEFAULT_TIMEZONE)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone(DEFAULT_TIMEZONE)


def parse_timezone(text: str | None) -> str | None:
    """The IANA name for a typed zone («Europe/Berlin», «берлин»), or None."""

    if not text:
        return None
    return _ZONES_BY_KEY.get(text.strip().casefold())


def zone_label(name: str) -> str:
    """A short name for the zone: the city from the menu, or the IANA name."""

    return TIMEZONE_CHOICES.get(name, name)


def zone_offset(name: str, at: datetime) -> str:
    """The zone's UTC offset at ``at``: «UTC+3», «UTC+5:30», «UTC»."""

    offset = at.astimezone(get_zone(name)).utcoffset()
    minutes = int(offset.total_seconds() // 60)
    if minutes == 0:
        return "UTC"
    sign = "+" if minutes > 0 else "-"
    hours, rest = divmod(abs(minutes), 60)
    return f"UTC{sign}{hours}" + (f":{rest:02d}" if rest else "")


def describe_zone(name: str, at: datetime) -> str:
    """The zone as shown to admins: «Москва (UTC+3)»."""

    label, offset = zone_label(name), zone_offset(name, at)
    return label if label == offset else f"{label} ({offset})"


# --- dates in the chat's zone -------------------------------------------------


def localize(naive: datetime, zone: str) -> datetime:
    """Read a wall-clock time in the zone; the result is in UTC.

    A time skipped by a DST change moves forward by the gap.
    """

    tz = get_zone(zone)
    return tz.normalize(tz.localize(naive)).astimezone(timezone.utc)


def chat_today(now: datetime, zone: str) -> date:
    """Today's date in the chat's zone."""

    return now.astimezone(get_zone(zone)).date()


def rotation_at(day: date, hour: int, zone: str) -> datetime:
    """The UTC moment of ``hour``:00 on ``day`` in the chat's zone."""

    return localize(datetime.combine(day, time(hour=hour)), zone)


def available_hours(day: date, now: datetime, zone: str) -> list[int]:
    """Hours of ``day`` that are still in the future."""

    return [hour for hour in range(24) if rotation_at(day, hour, zone) > now]


def upcoming_days(now: datetime, zone: str, count: int = 7) -> list[date]:
    """The next ``count`` days, starting today, that still have a free hour."""

    today = chat_today(now, zone)
    days = [today + timedelta(days=offset) for offset in range(count + 1)]
    return [day for day in days if available_hours(day, now, zone)][:count]


def with_hour(current: datetime, hour: int, now: datetime, zone: str) -> datetime:
    """Move the next rotation to ``hour``:00, keeping its day when possible.

    An overdue rotation moves to today; when the hour has already passed that
    day, the rotation moves to the next day.
    """

    day = max(current.astimezone(get_zone(zone)).date(), chat_today(now, zone))
    moved = rotation_at(day, hour, zone)
    return moved if moved > now else rotation_at(day + timedelta(days=1), hour, zone)


def day_label(day: date, now: datetime, zone: str) -> str:
    """A short button label: «Сегодня», «Завтра» or «Пт 13.11»."""

    offset = (day - chat_today(now, zone)).days
    if offset == 0:
        return "Сегодня"
    if offset == 1:
        return "Завтра"
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"


def format_chat_date(value: datetime, zone: str) -> str:
    """A stored date in the chat's zone, with the zone: «31.12.2026 18:00 (Москва)»."""

    local = value.astimezone(get_zone(zone)).strftime(DISPLAY_FORMAT)
    return f"{local} ({zone_label(zone)})"


def describe_settings(next_rotation: datetime, delta: int, zone: str) -> str:
    """The chat's schedule as shown to admins."""

    return (
        f"Ближайшая дата смены: {format_chat_date(next_rotation, zone)}.\n"
        f"Промежуток между сменами: {delta}д.\n"
        f"Часовой пояс: {describe_zone(zone, next_rotation)}."
    )


# --- typed values -------------------------------------------------------------


def parse_rotation_date(text: str, zone: str) -> datetime:
    """Parse ``DD/MM/YYYY HH:MM`` in the chat's zone into an aware UTC datetime.

    Raises ValueError when the text does not match the format.
    """

    return localize(datetime.strptime(text.strip(), INPUT_FORMAT), zone)


def example_rotation_date(now: datetime, zone: str) -> str:
    """A valid /set_date argument: tomorrow at 18:00 in the chat's zone."""

    tomorrow = chat_today(now, zone) + timedelta(days=1)
    return datetime.combine(tomorrow, time(hour=18)).strftime(INPUT_FORMAT)


def parse_delta(text: str | None) -> int | None:
    """Return the interval in days, or None unless it is a whole number in range."""

    if text is None:
        return None
    try:
        delta = int(text.strip())
    except ValueError:
        return None
    return delta if 1 <= delta <= MAX_DELTA_DAYS else None
