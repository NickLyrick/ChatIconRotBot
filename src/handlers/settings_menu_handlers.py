"""The /settings menu: change the rotation schedule with inline buttons.

Every button redraws the same message. Each action returns an optional short
notice that pops up for the admin who pressed the button.
"""

from datetime import date, datetime, timezone
from typing import Awaitable, Callable, Optional

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup

from src.database import Request
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
)
from src.utility.schedule import (
    available_hours,
    describe_settings,
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

    chat_settings = await request.get_chat_settings(chat_id=message.chat.id)
    if chat_settings is None:
        await message.reply(NOT_STARTED_TEXT)
        return

    next_rotation, delta, _ = chat_settings
    await message.reply(
        describe_settings(next_rotation, delta) + MAIN_HINT,
        reply_markup=build_main_keyboard(),
    )


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


async def _show_main(message: types.Message, request: Request, close: bool = False):
    """Redraw the current settings, with the main buttons unless closing."""

    chat_settings = await request.get_chat_settings(chat_id=message.chat.id)
    if chat_settings is None:
        await _edit(message, NOT_STARTED_TEXT)
        return

    next_rotation, delta, _ = chat_settings
    text = describe_settings(next_rotation, delta)
    if close:
        await _edit(message, text)
    else:
        await _edit(message, text + MAIN_HINT, build_main_keyboard())


async def _show_days(message: types.Message, now: datetime) -> None:
    await _edit(
        message,
        "Выберите день ближайшей смены:",
        build_day_keyboard(upcoming_days(now), now),
    )


async def _show_hours(message: types.Message, day: date, now: datetime) -> None:
    await _edit(
        message,
        f"Выберите час смены {day.strftime('%d.%m')} (МСК):",
        build_date_hour_keyboard(day, available_hours(day, now)),
    )


# --- button data --------------------------------------------------------------


def _chosen_day(data: SettingsCallbackData, now: datetime) -> Optional[date]:
    """The day from a button, if it is still one of the offered days."""

    if data.day is None:
        return None
    day = date.fromordinal(data.day)
    return day if day in upcoming_days(now) else None


def _chosen_hour(data: SettingsCallbackData) -> Optional[int]:
    return data.value if data.value is not None and 0 <= data.value <= 23 else None


# --- actions ------------------------------------------------------------------

Notice = Optional[str]


async def _main(message, request, data, now) -> Notice:
    await _show_main(message, request)


async def _close(message, request, data, now) -> Notice:
    await _show_main(message, request, close=True)


async def _delta(message, request, data, now) -> Notice:
    await _edit(message, "Выберите промежуток между сменами:", build_delta_keyboard())


async def _set_delta(message, request, data, now) -> Notice:
    notice = EXPIRED_TEXT
    if data.value in DELTA_CHOICES and await request.set_chat_delta(
        chat_id=message.chat.id, delta=data.value
    ):
        notice = f"Промежуток: {data.value}д. Начнёт действовать после ближайшей смены."
    await _show_main(message, request)
    return notice


async def _date(message, request, data, now) -> Notice:
    await _show_days(message, now)


async def _date_day(message, request, data, now) -> Notice:
    day = _chosen_day(data, now)
    if day is None:
        await _show_days(message, now)
        return DAY_GONE_TEXT
    await _show_hours(message, day, now)
    return None


async def _set_date(message, request, data, now) -> Notice:
    day, hour = _chosen_day(data, now), _chosen_hour(data)
    if day is None or hour is None:
        await _show_days(message, now)
        return DAY_GONE_TEXT

    new_date = rotation_at(day, hour)
    if new_date <= now:
        await _show_hours(message, day, now)
        return HOUR_GONE_TEXT

    notice = None
    if await request.set_chat_date(message.chat.id, new_date):
        notice = f"Ближайшая смена: {format_chat_date(new_date)} (МСК)"
    await _show_main(message, request)
    return notice


async def _time(message, request, data, now) -> Notice:
    chat_settings = await request.get_chat_settings(chat_id=message.chat.id)
    if chat_settings is None:
        await _edit(message, NOT_STARTED_TEXT)
        return None

    await _edit(
        message,
        f"Ближайшая смена: {format_chat_date(chat_settings[0])} (МСК).\n"
        "Выберите новый час (МСК). День сохранится, а если этот час уже прошёл, "
        "смена перенесётся на следующий день:",
        build_time_keyboard(),
    )
    return None


async def _set_time(message, request, data, now) -> Notice:
    hour = _chosen_hour(data)
    chat_settings = await request.get_chat_settings(chat_id=message.chat.id)

    notice = EXPIRED_TEXT if hour is None else None
    if hour is not None and chat_settings is not None:
        new_date = with_hour(chat_settings[0], hour, now)
        if await request.set_chat_date(message.chat.id, new_date):
            notice = f"Ближайшая смена: {format_chat_date(new_date)} (МСК)"
    await _show_main(message, request)
    return notice


Action = Callable[
    [types.Message, Request, SettingsCallbackData, datetime], Awaitable[Notice]
]

ACTIONS: dict[SettingsAction, Action] = {
    SettingsAction.MAIN: _main,
    SettingsAction.CLOSE: _close,
    SettingsAction.DELTA: _delta,
    SettingsAction.SET_DELTA: _set_delta,
    SettingsAction.DATE: _date,
    SettingsAction.DATE_DAY: _date_day,
    SettingsAction.SET_DATE: _set_date,
    SettingsAction.TIME: _time,
    SettingsAction.SET_TIME: _set_time,
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

    if callback.message is None or isinstance(
        callback.message, types.InaccessibleMessage
    ):
        # Telegram no longer gives the bot messages this old, so it cannot edit them.
        await callback.answer(EXPIRED_TEXT, show_alert=True)
        return

    action = ACTIONS[callback_data.action]
    notice = await action(callback.message, request, callback_data, _now())
    await callback.answer(notice)
