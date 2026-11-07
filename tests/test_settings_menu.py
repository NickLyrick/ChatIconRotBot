"""Tests for the /settings menu: button data, keyboards, button presses, permissions.

Handlers are called directly with stand-ins for the message, the button press
and :class:`src.database.Request`; the clock is fixed.
"""

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InaccessibleMessage

from src.bot.settings import settings
from src.database.connect import ChatSettings
from src.filters.filters import CheckPermissions
from src.handlers import settings_menu_handlers as menu
from src.handlers.schedule_handlers import NOT_STARTED_TEXT
from src.keyboards.inline import (
    DELTA_CHOICES,
    SettingsAction,
    SettingsCallbackData,
    build_date_hour_keyboard,
    build_day_keyboard,
    build_delta_keyboard,
    build_main_keyboard,
    build_time_keyboard,
    build_timezone_keyboard,
)
from src.utility.schedule import TIMEZONE_CHOICES, upcoming_days

UTC = timezone.utc
CHAT_ID = -1001234567890
USER_ID = 111
MSK = "Europe/Moscow"
VLAD = "Asia/Vladivostok"

# 15:30 in Moscow on Saturday, 7 November 2026.
NOW = datetime(2026, 11, 7, 12, 30, tzinfo=UTC)
TODAY = date(2026, 11, 7)
TOMORROW = date(2026, 11, 8)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(menu, "_now", lambda: NOW)


class FakeMessage:
    """The menu message: records what it was redrawn to."""

    def __init__(self, not_modified: bool = False):
        self.chat = SimpleNamespace(id=CHAT_ID)
        self.replies: list[tuple[str, object]] = []
        self.text: str | None = None
        self.markup = None
        self.not_modified = not_modified

    async def reply(self, text: str, reply_markup=None, **_) -> None:
        self.replies.append((text, reply_markup))

    async def edit_text(self, text: str, reply_markup=None, **_) -> None:
        if self.not_modified:
            raise TelegramBadRequest(
                method=None, message="Bad Request: message is not modified"
            )
        self.text, self.markup = text, reply_markup


class FakeCallback:
    """A button press; records the pop-up answer."""

    def __init__(self, message=None, user_id: int = USER_ID):
        self.message = message if message is not None else FakeMessage()
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[tuple[str | None, bool]] = []

    async def answer(self, text: str | None = None, show_alert: bool = False, **_):
        self.answers.append((text, show_alert))


class FakeRequest:
    """Chat settings in memory."""

    def __init__(self, registered=True, date_=None, delta=1, zone=MSK):
        self.registered = registered
        self.date = date_ or datetime(2026, 11, 10, 15, 0, tzinfo=UTC)  # 10.11 18:00 MSK
        self.delta = delta
        self.zone = zone

    async def set_chat_date(self, chat_id, date):
        if self.registered:
            self.date = date
        return self.registered

    async def set_chat_delta(self, chat_id, delta):
        if self.registered:
            self.delta = delta
        return self.registered

    async def set_chat_timezone(self, chat_id, zone):
        if self.registered:
            self.zone = zone
        return self.registered

    async def get_chat_settings(self, chat_id):
        if not self.registered:
            return None
        return ChatSettings(self.date, self.delta, self.zone, None)


def buttons(markup) -> list[tuple[str, SettingsCallbackData]]:
    return [
        (button.text, SettingsCallbackData.unpack(button.callback_data))
        for row in markup.inline_keyboard
        for button in row
    ]


async def press(request, action, message=None, **data):
    callback = FakeCallback(message)
    await menu.settings_button(
        callback, SettingsCallbackData(action=action, **data), request
    )
    return callback


# --- button data and keyboards ------------------------------------------------


def test_callback_data_round_trip_fits_telegram_limit():
    data = SettingsCallbackData(
        action=SettingsAction.SET_DATE, value=23, day=TOMORROW.toordinal()
    )

    packed = data.pack()

    assert len(packed.encode()) <= 64
    assert SettingsCallbackData.unpack(packed) == data


def test_main_keyboard():
    assert [(text, data.action) for text, data in buttons(build_main_keyboard())] == [
        ("Интервал", SettingsAction.DELTA),
        ("Дата", SettingsAction.DATE),
        ("Время", SettingsAction.TIME),
        ("Часовой пояс", SettingsAction.TIMEZONE),
        ("Закрыть", SettingsAction.CLOSE),
    ]


def test_every_timezone_button_fits_telegram_limit():
    for zone in TIMEZONE_CHOICES:
        data = SettingsCallbackData(action=SettingsAction.SET_TIMEZONE, zone=zone)
        assert len(data.pack().encode()) <= 64
        assert SettingsCallbackData.unpack(data.pack()).zone == zone


def test_timezone_keyboard_shows_offsets():
    pressed = buttons(build_timezone_keyboard(NOW))

    assert [data.zone for _, data in pressed[:-1]] == list(TIMEZONE_CHOICES)
    assert ("Москва (UTC+3)", MSK) in [(text, data.zone) for text, data in pressed]
    assert ("Берлин (UTC+1)", "Europe/Berlin") in [(text, data.zone) for text, data in pressed]
    assert pressed[-1][1].action == SettingsAction.MAIN


def test_delta_keyboard_offers_the_choices_and_back():
    pressed = buttons(build_delta_keyboard())

    assert [data.value for _, data in pressed[:-1]] == list(DELTA_CHOICES)
    assert pressed[-1][1].action == SettingsAction.MAIN


def test_day_keyboard_labels_and_days():
    pressed = buttons(build_day_keyboard(upcoming_days(NOW, MSK), NOW, MSK))

    assert [text for text, _ in pressed[:3]] == ["Сегодня", "Завтра", "Пн 09.11"]
    assert pressed[0][1].day == TODAY.toordinal()
    assert pressed[-1][1].action == SettingsAction.MAIN


def test_date_hour_keyboard_carries_day_and_hour():
    pressed = buttons(build_date_hour_keyboard(TODAY, [16, 17]))

    assert [(text, data.value, data.day) for text, data in pressed[:-1]] == [
        ("16:00", 16, TODAY.toordinal()),
        ("17:00", 17, TODAY.toordinal()),
    ]
    assert pressed[-1][1].action == SettingsAction.DATE


def test_time_keyboard_has_every_hour():
    pressed = buttons(build_time_keyboard())

    assert [data.value for _, data in pressed[:-1]] == list(range(24))


# --- /settings ----------------------------------------------------------------


async def test_settings_command_shows_settings_and_main_menu():
    message = FakeMessage()

    await menu.settings_menu(message, FakeRequest(delta=3))

    text, markup = message.replies[0]
    assert "10.11.2026 18:00 (Москва)" in text
    assert "3д." in text
    assert buttons(markup)[0][1].action == SettingsAction.DELTA


async def test_settings_command_in_unregistered_chat_asks_for_start():
    message = FakeMessage()

    await menu.settings_menu(message, FakeRequest(registered=False))

    assert message.replies == [(NOT_STARTED_TEXT, None)]


# --- interval -----------------------------------------------------------------


async def test_choosing_an_interval_saves_it_and_returns_to_main():
    request = FakeRequest()

    callback = await press(request, SettingsAction.SET_DELTA, value=7)

    assert request.delta == 7
    assert "7д." in callback.message.text
    assert buttons(callback.message.markup)[0][1].action == SettingsAction.DELTA
    assert "7д." in callback.answers[0][0]


async def test_interval_outside_the_choices_is_ignored():
    request = FakeRequest(delta=2)

    callback = await press(request, SettingsAction.SET_DELTA, value=1000)

    assert request.delta == 2
    assert callback.answers == [(menu.EXPIRED_TEXT, False)]


# --- date ---------------------------------------------------------------------


async def test_date_flow_sets_day_and_hour():
    request = FakeRequest()

    days = await press(request, SettingsAction.DATE)
    assert buttons(days.message.markup)[1][0] == "Завтра"

    hours = await press(request, SettingsAction.DATE_DAY, day=TOMORROW.toordinal())
    assert "08.11" in hours.message.text
    assert len(buttons(hours.message.markup)) == 24 + 1

    chosen = await press(
        request, SettingsAction.SET_DATE, day=TOMORROW.toordinal(), value=9
    )
    assert request.date == datetime(2026, 11, 8, 6, 0, tzinfo=UTC)
    assert chosen.answers == [("Ближайшая смена: 08.11.2026 09:00 (Москва)", False)]
    assert "08.11.2026 09:00 (Москва)" in chosen.message.text


async def test_today_offers_only_future_hours():
    callback = await press(FakeRequest(), SettingsAction.DATE_DAY, day=TODAY.toordinal())

    hours = [data.value for _, data in buttons(callback.message.markup)[:-1]]
    assert hours == list(range(16, 24))


async def test_hour_that_has_passed_is_refused():
    request = FakeRequest()
    before = request.date

    callback = await press(
        request, SettingsAction.SET_DATE, day=TODAY.toordinal(), value=10
    )

    assert request.date == before
    assert callback.answers == [(menu.HOUR_GONE_TEXT, False)]
    assert callback.message.text.startswith("Выберите час")


@pytest.mark.parametrize("day", [date(2026, 11, 6), date(2026, 12, 31)])
async def test_day_that_is_not_offered_is_refused(day):
    request = FakeRequest()
    before = request.date

    callback = await press(request, SettingsAction.SET_DATE, day=day.toordinal(), value=12)

    assert request.date == before
    assert callback.answers == [(menu.DAY_GONE_TEXT, False)]
    assert callback.message.text == "Выберите день ближайшей смены:"


# --- time ---------------------------------------------------------------------


async def test_time_menu_shows_current_rotation():
    callback = await press(FakeRequest(), SettingsAction.TIME)

    assert "10.11.2026 18:00 (Москва)" in callback.message.text
    assert len(buttons(callback.message.markup)) == 24 + 1


async def test_choosing_a_time_keeps_the_day():
    request = FakeRequest()

    callback = await press(request, SettingsAction.SET_TIME, value=21)

    assert request.date == datetime(2026, 11, 10, 18, 0, tzinfo=UTC)
    assert callback.answers == [("Ближайшая смена: 10.11.2026 21:00 (Москва)", False)]


async def test_invalid_hour_is_ignored():
    request = FakeRequest()
    before = request.date

    callback = await press(request, SettingsAction.SET_TIME, value=24)

    assert request.date == before
    assert callback.answers == [(menu.EXPIRED_TEXT, False)]


# --- navigation and edge cases ------------------------------------------------


async def test_close_removes_the_buttons():
    callback = await press(FakeRequest(), SettingsAction.CLOSE)

    assert callback.message.markup is None
    assert "Что поменять?" not in callback.message.text


async def test_unchanged_menu_is_not_an_error():
    callback = await press(FakeRequest(), SettingsAction.MAIN, message=FakeMessage(True))

    assert callback.answers == [(None, False)]


async def test_unregistered_chat_shows_start_hint():
    request = FakeRequest(registered=False)

    callback = await press(request, SettingsAction.SET_TIME, value=12)

    assert callback.message.text == NOT_STARTED_TEXT
    assert callback.answers == [(None, False)]


async def test_old_menu_message_asks_to_reopen():
    old = InaccessibleMessage(chat={"id": CHAT_ID, "type": "supergroup"}, message_id=1)

    callback = await press(FakeRequest(), SettingsAction.MAIN, message=old)

    assert callback.answers == [(menu.EXPIRED_TEXT, True)]


# --- permissions --------------------------------------------------------------


class FakeBot:
    def __init__(self, status):
        self.status = status

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status=self.status)


@pytest.fixture(name="no_bot_admins")
def fixture_no_bot_admins(monkeypatch):
    monkeypatch.setattr(settings.bot, "admin_ids", [])


@pytest.mark.usefixtures("no_bot_admins")
async def test_chat_owner_may_press_buttons():
    allowed = await CheckPermissions()(FakeCallback(), FakeBot(ChatMemberStatus.CREATOR))

    assert allowed is True


@pytest.mark.usefixtures("no_bot_admins")
async def test_other_members_get_an_alert():
    callback = FakeCallback()

    allowed = await CheckPermissions()(callback, FakeBot(ChatMemberStatus.MEMBER))

    assert allowed is False
    assert callback.answers == [(CheckPermissions.DENIED_TEXT, True)]


async def test_bot_admin_may_press_buttons(monkeypatch):
    monkeypatch.setattr(settings.bot, "admin_ids", [USER_ID])

    allowed = await CheckPermissions()(FakeCallback(), FakeBot(ChatMemberStatus.MEMBER))

    assert allowed is True


# --- time zone ----------------------------------------------------------------


async def test_timezone_menu_shows_the_current_zone():
    callback = await press(FakeRequest(zone=VLAD), SettingsAction.TIMEZONE)

    assert callback.message.text.startswith("Сейчас: Владивосток (UTC+10).")
    assert len(buttons(callback.message.markup)) == len(TIMEZONE_CHOICES) + 1


async def test_choosing_a_zone_saves_it_and_keeps_the_rotation_moment():
    request = FakeRequest()
    before = request.date

    callback = await press(request, SettingsAction.SET_TIMEZONE, zone=VLAD)

    assert request.zone == VLAD
    assert request.date == before
    assert callback.answers == [
        (
            "Часовой пояс: Владивосток (UTC+10). "
            "Ближайшая смена: 11.11.2026 01:00 (Владивосток)",
            False,
        )
    ]
    assert "Часовой пояс: Владивосток (UTC+10)." in callback.message.text


async def test_zone_outside_the_menu_is_ignored():
    request = FakeRequest()

    callback = await press(request, SettingsAction.SET_TIMEZONE, zone="Europe/Paris")

    assert request.zone == MSK
    assert callback.answers == [(menu.EXPIRED_TEXT, False)]


async def test_days_and_hours_follow_the_chat_zone():
    """At 22:30 in Vladivostok only 23:00 is left today."""

    request = FakeRequest(zone=VLAD)

    hours = await press(request, SettingsAction.DATE_DAY, day=TODAY.toordinal())
    assert [data.value for _, data in buttons(hours.message.markup)[:-1]] == [23]

    chosen = await press(request, SettingsAction.SET_DATE, day=TODAY.toordinal(), value=23)
    assert request.date == datetime(2026, 11, 7, 13, 0, tzinfo=UTC)
    assert chosen.answers == [("Ближайшая смена: 07.11.2026 23:00 (Владивосток)", False)]


async def test_time_keeps_the_day_in_the_chat_zone():
    # 10.11 15:00 UTC is 11.11 01:00 in Vladivostok.
    request = FakeRequest(zone=VLAD)

    await press(request, SettingsAction.SET_TIME, value=9)

    assert request.date == datetime(2026, 11, 10, 23, 0, tzinfo=UTC)  # 11.11 09:00
