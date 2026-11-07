"""Tests for the /start, /set_date, /set_delta and /show_settings handlers.

The handlers are called directly (filters are not involved) with stand-ins for
the message and for :class:`src.database.Request`.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.handlers import schedule_handlers as handlers
from src.utility.schedule import MAX_DELTA_DAYS

UTC = timezone.utc
CHAT_ID = -1001234567890


class FakeMessage:
    """Records the bot's replies."""

    def __init__(self):
        self.chat = SimpleNamespace(id=CHAT_ID)
        self.replies: list[str] = []
        self.photos: list[tuple[str, str]] = []

    async def reply(self, text: str, **_) -> None:
        self.replies.append(text)

    answer = reply

    async def reply_photo(self, photo: str, caption: str, **_) -> None:
        self.photos.append((photo, caption))


class FakeRequest:
    """Keeps chat settings in memory; ``registered`` mimics the chats table row."""

    def __init__(self, registered: bool = True, date=None, delta=1, photo=None):
        self.registered = registered
        self.date = date or datetime(2026, 12, 31, 15, 0, tzinfo=UTC)
        self.delta = delta
        self.photo = photo
        self.added: list[tuple] = []

    async def add_chat(self, chat_id, date, delta):
        self.added.append((chat_id, date, delta))
        self.registered = True

    async def set_chat_date(self, chat_id, date):
        if self.registered:
            self.date = date
        return self.registered

    async def set_chat_delta(self, chat_id, delta):
        if self.registered:
            self.delta = delta
        return self.registered

    async def get_chat_settings(self, chat_id):
        if not self.registered:
            return None
        return [self.date, self.delta, self.photo]


def command(args):
    return SimpleNamespace(args=args)


def future_date_text(days: int = 2) -> tuple[str, datetime]:
    """A /set_date argument some days ahead (Moscow time) and its UTC value."""

    moscow = datetime.now(UTC) + timedelta(hours=3) + timedelta(days=days)
    moscow = moscow.replace(hour=18, minute=0, second=0, microsecond=0)
    return moscow.strftime("%d/%m/%Y %H:%M"), (moscow - timedelta(hours=3)).replace(
        tzinfo=UTC
    )


# --- /start -------------------------------------------------------------------


async def test_start_registers_the_chat():
    message, request = FakeMessage(), FakeRequest(registered=False)

    await handlers.start(message, request)

    assert [chat_id for chat_id, _, _ in request.added] == [CHAT_ID]
    assert request.added[0][2] == 1
    assert message.replies == ["Да начнётся охота!"]


# --- /set_date ----------------------------------------------------------------


async def test_set_date_stores_moscow_time_as_utc_and_echoes_it():
    message, request = FakeMessage(), FakeRequest()
    text, expected = future_date_text()

    await handlers.set_date(message, command(text), request)

    assert request.date == expected
    assert len(message.replies) == 1
    assert text.replace("/", ".") in message.replies[0]
    assert "(МСК)" in message.replies[0]


@pytest.mark.parametrize("args", [None, ""])
async def test_set_date_without_arguments_shows_usage(args):
    message, request = FakeMessage(), FakeRequest()
    before = request.date

    await handlers.set_date(message, command(args), request)

    assert request.date == before
    assert "/set_date ДД/ММ/ГГГГ ЧЧ:ММ" in message.replies[0]


async def test_set_date_rejects_malformed_date():
    message, request = FakeMessage(), FakeRequest()
    before = request.date

    await handlers.set_date(message, command("2026-12-31 18:00"), request)

    assert request.date == before
    assert message.replies[0].startswith("Неверный формат даты.")


async def test_set_date_rejects_past_date():
    message, request = FakeMessage(), FakeRequest()
    before = request.date

    await handlers.set_date(message, command("01/01/2020 12:00"), request)

    assert request.date == before
    assert "в прошлом" in message.replies[0]


async def test_set_date_in_unregistered_chat_asks_for_start():
    message, request = FakeMessage(), FakeRequest(registered=False)

    await handlers.set_date(message, command(future_date_text()[0]), request)

    assert message.replies == [handlers.NOT_STARTED_TEXT]


# --- /set_delta ---------------------------------------------------------------


async def test_set_delta_stores_the_interval():
    message, request = FakeMessage(), FakeRequest()

    await handlers.set_delta(message, command("3"), request)

    assert request.delta == 3
    assert "3д." in message.replies[0]


@pytest.mark.parametrize("args", [None, "0", "-1", "2.5", "abc", str(MAX_DELTA_DAYS + 1)])
async def test_set_delta_rejects_invalid_interval(args):
    message, request = FakeMessage(), FakeRequest(delta=5)

    await handlers.set_delta(message, command(args), request)

    assert request.delta == 5
    assert f"от 1 до {MAX_DELTA_DAYS}" in message.replies[0]


async def test_set_delta_in_unregistered_chat_asks_for_start():
    message, request = FakeMessage(), FakeRequest(registered=False)

    await handlers.set_delta(message, command("3"), request)

    assert message.replies == [handlers.NOT_STARTED_TEXT]


# --- /show_settings -----------------------------------------------------------


async def test_show_settings_shows_moscow_time():
    message = FakeMessage()
    request = FakeRequest(date=datetime(2026, 12, 31, 15, 0, tzinfo=UTC), delta=4)

    await handlers.show_settings(message, request)

    assert message.replies == [
        "Ближайшая дата смены: 31.12.2026 18:00 (МСК).\n"
        "Промежуток между сменами: 4д.\n"
        "Стандартный аватар не установлен"
    ]


async def test_show_settings_sends_default_avatar():
    message, request = FakeMessage(), FakeRequest(photo="photo-id")

    await handlers.show_settings(message, request)

    assert message.photos[0][0] == "photo-id"
    assert "31.12.2026 18:00 (МСК)" in message.photos[0][1]


async def test_show_settings_in_unregistered_chat_asks_for_start():
    message, request = FakeMessage(), FakeRequest(registered=False)

    await handlers.show_settings(message, request)

    assert message.replies == [handlers.NOT_STARTED_TEXT]


async def test_settings_set_by_commands_are_shown_back():
    """The date typed into /set_date is the date /show_settings displays."""

    message, request = FakeMessage(), FakeRequest()
    text, _ = future_date_text(days=10)

    await handlers.set_date(message, command(text), request)
    await handlers.show_settings(message, request)

    assert text.replace("/", ".") in message.replies[-1]
