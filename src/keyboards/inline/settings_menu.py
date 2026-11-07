"""Inline keyboards of the /settings menu."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utility.schedule import day_label

DELTA_CHOICES = (1, 2, 3, 4, 5, 6, 7, 10, 14, 21, 30)


class SettingsAction(str, Enum):
    """What a button of the settings menu does."""

    MAIN = "main"  # show the settings and the main buttons
    DELTA = "delta"  # choose the interval
    SET_DELTA = "set_delta"
    DATE = "date"  # choose the day of the next rotation
    DATE_DAY = "date_day"  # choose the hour on the chosen day
    SET_DATE = "set_date"
    TIME = "time"  # choose a new hour for the next rotation
    SET_TIME = "set_time"
    CLOSE = "close"


class SettingsCallbackData(CallbackData, prefix="settings"):
    """Callback data of the settings menu."""

    action: SettingsAction
    # Interval in days for SET_DELTA, hour for SET_DATE and SET_TIME.
    value: Optional[int] = None
    # Chosen day as date.toordinal() for DATE_DAY and SET_DATE.
    day: Optional[int] = None


def _button(builder: InlineKeyboardBuilder, text: str, action: SettingsAction, **data):
    builder.button(text=text, callback_data=SettingsCallbackData(action=action, **data))


def _hours(builder: InlineKeyboardBuilder, hours: list[int], action: SettingsAction, **data):
    for hour in hours:
        _button(builder, f"{hour:02d}:00", action, value=hour, **data)


def build_main_keyboard() -> InlineKeyboardMarkup:
    """Buttons of the main menu."""

    builder = InlineKeyboardBuilder()
    _button(builder, "Интервал", SettingsAction.DELTA)
    _button(builder, "Дата", SettingsAction.DATE)
    _button(builder, "Время", SettingsAction.TIME)
    _button(builder, "Закрыть", SettingsAction.CLOSE)
    builder.adjust(3, 1)
    return builder.as_markup()


def build_delta_keyboard() -> InlineKeyboardMarkup:
    """Interval choices, in days."""

    builder = InlineKeyboardBuilder()
    for delta in DELTA_CHOICES:
        _button(builder, f"{delta}д.", SettingsAction.SET_DELTA, value=delta)
    _button(builder, "« Назад", SettingsAction.MAIN)
    builder.adjust(6, 5, 1)
    return builder.as_markup()


def build_day_keyboard(days: list[date], now: datetime) -> InlineKeyboardMarkup:
    """Day choices for the next rotation."""

    builder = InlineKeyboardBuilder()
    for day in days:
        _button(builder, day_label(day, now), SettingsAction.DATE_DAY, day=day.toordinal())
    _button(builder, "« Назад", SettingsAction.MAIN)
    builder.adjust(*([2] * ((len(days) + 1) // 2)), 1)
    return builder.as_markup()


def build_date_hour_keyboard(day: date, hours: list[int]) -> InlineKeyboardMarkup:
    """Hour choices on the chosen day."""

    builder = InlineKeyboardBuilder()
    _hours(builder, hours, SettingsAction.SET_DATE, day=day.toordinal())
    _button(builder, "« Назад", SettingsAction.DATE)
    builder.adjust(*([6] * ((len(hours) + 5) // 6)), 1)
    return builder.as_markup()


def build_time_keyboard() -> InlineKeyboardMarkup:
    """Hour choices that keep the day of the next rotation."""

    builder = InlineKeyboardBuilder()
    _hours(builder, list(range(24)), SettingsAction.SET_TIME)
    _button(builder, "« Назад", SettingsAction.MAIN)
    builder.adjust(6, 6, 6, 6, 1)
    return builder.as_markup()
