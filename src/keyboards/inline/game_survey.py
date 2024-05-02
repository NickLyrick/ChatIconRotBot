from enum import IntEnum, auto
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SurveyState(IntEnum):
    """State of Survey."""

    IDLE = auto()
    STARTED = auto()
    GAME_SCORED = auto()
    PICTURE_SCORED = auto()
    DIFFICULTY_SCORED = auto()
    CANCELED = auto()


class GameSurveyCallbackData(CallbackData, prefix="game_survey"):
    """Callback Data For Game Survey."""

    # state of survey
    state: SurveyState = None

    # id of person who started survey
    user_id: Optional[int] = None

    # platinum info
    history_id: Optional[int] = None
    hunter_id: Optional[int] = None

    # scores for platinum
    game_score: Optional[int] = None
    picture_score: Optional[int] = None
    difficulty_score: Optional[int] = None


def build_start_survey_keyboard(
    text: str,
    callback_data: GameSurveyCallbackData,
) -> InlineKeyboardMarkup:
    """Get Start Survey Keyboard."""

    if callback_data.state is None:
        callback_data.state = SurveyState.IDLE
    else:
        callback_data.state = SurveyState.STARTED

    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback_data.pack())

    return builder.as_markup()


def build_game_score_keyboard(
    callback_data: GameSurveyCallbackData,
) -> InlineKeyboardMarkup:
    """Get Game Score Keyboard."""

    builder = InlineKeyboardBuilder()

    for i in range(1, 11):
        callback_data.state = SurveyState.GAME_SCORED
        callback_data.game_score = i
        builder.button(text=str(i), callback_data=callback_data.pack())

    callback_data.state = SurveyState.CANCELED
    builder.button(text="Отмена", callback_data=callback_data.pack())

    builder.adjust(5, 5, 1)

    return builder.as_markup()


def build_picture_score_keyboard(
    callback_data: GameSurveyCallbackData,
) -> InlineKeyboardMarkup:
    """Get Picture Score Keyboard."""

    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        callback_data.state = SurveyState.PICTURE_SCORED
        callback_data.picture_score = i
        builder.button(text=str(i), callback_data=callback_data.pack())

    callback_data.state = SurveyState.STARTED
    builder.button(text="Назад", callback_data=callback_data.pack())

    callback_data.state = SurveyState.CANCELED
    builder.button(text="Отмена", callback_data=callback_data.pack())

    builder.adjust(5, 5, 2)

    return builder.as_markup()


def build_difficulty_score_keyboard(
    callback_data: GameSurveyCallbackData,
) -> InlineKeyboardMarkup:
    """Get Difficulty Score Keyboard."""

    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        callback_data.state = SurveyState.DIFFICULTY_SCORED
        callback_data.difficulty_score = i
        builder.button(text=str(i), callback_data=callback_data.pack())

    callback_data.difficulty_score = None
    builder.button(text="Пропустить", callback_data=callback_data.pack())

    if callback_data.user_id != callback_data.hunter_id:
        callback_data.state = SurveyState.GAME_SCORED
    else:
        callback_data.state = SurveyState.CANCELED

    builder.button(text="Назад", callback_data=callback_data.pack())

    callback_data.state = SurveyState.CANCELED
    builder.button(text="Отмена", callback_data=callback_data.pack())

    builder.adjust(5, 5, 1, 2)

    return builder.as_markup()
