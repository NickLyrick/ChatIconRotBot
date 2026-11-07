"""The /settings menu: change the rotation schedule with inline buttons.

Every button redraws the same message. Each action returns an optional short
notice that pops up for the admin who pressed the button. Days and hours are
in the chat's time zone.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Awaitable, Callable, Optional

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup

from src.database import Request
from src.database.connect import ChatSettings
from src.filters import my_filters
from src.handlers.schedule_handlers import NOT_STARTED_TEXT, error_handler
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
from src.utility.schedule import (
    TIMEZONE_CHOICES,
    available_hours,
    describe_settings,
    describe_zone,
    format_chat_date,
    rotation_at,
    upcoming_days,
    with_hour,
)

settings_router = Router(name=__name__)
settings_router.error()(error_handler)

MAIN_HINT = "\n\nЧто поменять?"
EXPIRED_TEXT = "Меню устарело, вызовите /settings ещё раз"
DAY_GONE_TEXT = "Этот день уже недоступен, выберите другой"
HOUR_GONE_TEXT = "Это время уже прошло, выберите другое"


def _now() -> datetime:
    return datetime.now(timezone.utc)


@settings_router.message(
    Command("settings"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def settings_menu(message: types.Message, request: Request) -> None:
    """Open the settings menu."""

    chat = await request.get_chat_settings(chat_id=message.chat.id)
    if chat is None:
        await message.reply(NOT_STARTED_TEXT)
        return

    await message.reply(
        describe_settings(chat.date, chat.delta, chat.timezone) + MAIN_HINT,
        reply_markup=build_main_keyboard(),
    )


@dataclass
class Press:
    """A button press: where to redraw, what was pressed, the chat's settings."""

    message: types.Message
    request: Request
    data: SettingsCallbackData
    now: datetime
    chat: ChatSettings

    @property
    def zone(self) -> str:
        """The chat's IANA time zone."""
        return self.chat.timezone

    def date_text(self, value: datetime) -> str:
        """A date in the chat's zone, with the zone's name."""
        return format_chat_date(value, self.zone)


# --- drawing ------------------------------------------------------------------


async def _edit(
    message: types.Message, text: str, markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    """Redraw the menu message; an unchanged menu is not an error."""

    try:
        await message.edit_text(text=text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def _show_main(press: Press, close: bool = False) -> None:
    """Redraw the current settings, with the main buttons unless closing."""

    chat = await press.request.get_chat_settings(chat_id=press.message.chat.id)
    if chat is None:
        await _edit(press.message, NOT_STARTED_TEXT)
        return

    text = describe_settings(chat.date, chat.delta, chat.timezone)
    if close:
        await _edit(press.message, text)
    else:
        await _edit(press.message, text + MAIN_HINT, build_main_keyboard())


async def _show_days(press: Press) -> None:
    await _edit(
        press.message,
        "Выберите день ближайшей смены:",
        build_day_keyboard(upcoming_days(press.now, press.zone), press.now, press.zone),
    )


async def _show_hours(press: Press, day: date) -> None:
    await _edit(
        press.message,
        f"Выберите час смены {day.strftime('%d.%m')} ({describe_zone(press.zone, press.now)}):",
        build_date_hour_keyboard(day, available_hours(day, press.now, press.zone)),
    )


# --- button data --------------------------------------------------------------


def _chosen_day(press: Press) -> Optional[date]:
    """The day from a button, if it is still one of the offered days."""

    if press.data.day is None:
        return None
    day = date.fromordinal(press.data.day)
    return day if day in upcoming_days(press.now, press.zone) else None


def _chosen_hour(press: Press) -> Optional[int]:
    value = press.data.value
    return value if value is not None and 0 <= value <= 23 else None


# --- actions ------------------------------------------------------------------

Notice = Optional[str]


async def _main(press: Press) -> Notice:
    await _show_main(press)


async def _close(press: Press) -> Notice:
    await _show_main(press, close=True)


async def _delta(press: Press) -> Notice:
    await _edit(press.message, "Выберите промежуток между сменами:", build_delta_keyboard())


async def _set_delta(press: Press) -> Notice:
    notice = EXPIRED_TEXT
    delta = press.data.value
    if delta in DELTA_CHOICES and await press.request.set_chat_delta(
        chat_id=press.message.chat.id, delta=delta
    ):
        notice = f"Промежуток: {delta}д. Начнёт действовать после ближайшей смены."
    await _show_main(press)
    return notice


async def _date(press: Press) -> Notice:
    await _show_days(press)


async def _date_day(press: Press) -> Notice:
    day = _chosen_day(press)
    if day is None:
        await _show_days(press)
        return DAY_GONE_TEXT
    await _show_hours(press, day)
    return None


async def _set_date(press: Press) -> Notice:
    day, hour = _chosen_day(press), _chosen_hour(press)
    if day is None or hour is None:
        await _show_days(press)
        return DAY_GONE_TEXT

    new_date = rotation_at(day, hour, press.zone)
    if new_date <= press.now:
        await _show_hours(press, day)
        return HOUR_GONE_TEXT

    notice = None
    if await press.request.set_chat_date(press.message.chat.id, new_date):
        notice = f"Ближайшая смена: {press.date_text(new_date)}"
    await _show_main(press)
    return notice


async def _time(press: Press) -> Notice:
    await _edit(
        press.message,
        f"Ближайшая смена: {press.date_text(press.chat.date)}.\n"
        f"Выберите новый час ({describe_zone(press.zone, press.now)}). "
        "День сохранится, а если этот час уже прошёл, "
        "смена перенесётся на следующий день:",
        build_time_keyboard(),
    )


async def _set_time(press: Press) -> Notice:
    hour = _chosen_hour(press)
    notice = EXPIRED_TEXT
    if hour is not None:
        new_date = with_hour(press.chat.date, hour, press.now, press.zone)
        notice = None
        if await press.request.set_chat_date(press.message.chat.id, new_date):
            notice = f"Ближайшая смена: {press.date_text(new_date)}"
    await _show_main(press)
    return notice


async def _timezone(press: Press) -> Notice:
    await _edit(
        press.message,
        f"Сейчас: {describe_zone(press.zone, press.now)}.\n"
        "Выберите часовой пояс чата. Время ближайшей смены не сдвинется, "
        "изменится только то, как оно показывается и вводится.\n"
        "Другого пояса нет в списке? /set_timezone Europe/Berlin",
        build_timezone_keyboard(press.now),
    )


async def _set_timezone(press: Press) -> Notice:
    zone = press.data.zone
    notice = EXPIRED_TEXT
    if zone in TIMEZONE_CHOICES and await press.request.set_chat_timezone(
        press.message.chat.id, zone
    ):
        notice = (
            f"Часовой пояс: {describe_zone(zone, press.now)}. "
            f"Ближайшая смена: {format_chat_date(press.chat.date, zone)}"
        )
    await _show_main(press)
    return notice


ACTIONS: dict[SettingsAction, Callable[[Press], Awaitable[Notice]]] = {
    SettingsAction.MAIN: _main,
    SettingsAction.CLOSE: _close,
    SettingsAction.DELTA: _delta,
    SettingsAction.SET_DELTA: _set_delta,
    SettingsAction.DATE: _date,
    SettingsAction.DATE_DAY: _date_day,
    SettingsAction.SET_DATE: _set_date,
    SettingsAction.TIME: _time,
    SettingsAction.SET_TIME: _set_time,
    SettingsAction.TIMEZONE: _timezone,
    SettingsAction.SET_TIMEZONE: _set_timezone,
}


@settings_router.callback_query(
    SettingsCallbackData.filter(), my_filters.check_permissions
)
async def settings_button(
    callback: types.CallbackQuery,
    callback_data: SettingsCallbackData,
    request: Request,
) -> None:
    """Handle a press on a settings menu button."""

    message = callback.message
    if message is None or isinstance(message, types.InaccessibleMessage):
        # Telegram no longer gives the bot messages this old, so it cannot edit them.
        await callback.answer(EXPIRED_TEXT, show_alert=True)
        return

    chat = await request.get_chat_settings(chat_id=message.chat.id)
    if chat is None:
        await _edit(message, NOT_STARTED_TEXT)
        await callback.answer()
        return

    press = Press(message, request, callback_data, _now(), chat)
    notice = await ACTIONS[callback_data.action](press)
    await callback.answer(notice)
