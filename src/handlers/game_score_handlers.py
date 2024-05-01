from aiogram import F, Router
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.utils import formatting

from src.database import Request

from ..keyboards.inline import (
    GameSurveyCallbackData,
    SurveyState,
    build_difficulty_score_keyboard,
    build_game_score_keyboard,
    build_picture_score_keyboard,
    build_start_survey_keyboard,
)

game_score_router = Router()


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.CANCELED)
)
async def process_cancel(
    callback_query: CallbackQuery, callback_data: GameSurveyCallbackData
) -> None:
    """Process Cancel Callback."""

    await callback_query.answer()
    await callback_query.message.edit_text(
        text="Оценка отменена.",
        reply_markup=build_start_survey_keyboard(
            text="Оценить Заново", callback_data=callback_data
        ),
    )


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.IDLE)
)
async def start_survey(
    callback_query: CallbackQuery,
    callback_data: GameSurveyCallbackData
) -> None:
    """Start Survey Callback."""

    await callback_query.answer()

    callback_data.user_id = callback_query.from_user.id

    await callback_query.bot.send_photo(
        chat_id=callback_data.user_id,
        photo=callback_data.photo_id,
        text=f"Оцените игру {callback_data.game}",
        reply_markup=build_start_survey_keyboard(
            text="Оценить",
            callback_data=callback_data,
        ),
    )


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.STARTED)
)
async def process_first_step(
    callback_query: CallbackQuery, callback_data: GameSurveyCallbackData
) -> None:
    """Start Game Scoring or Skip to Difficulty Score Callback."""

    await callback_query.answer()

    if callback_data.hunter_id != callback_data.user_id:
        await callback_query.message.edit_text(
            text="Оцените Игру от 1 до 10",
            reply_markup=build_game_score_keyboard(callback_data),
        )
    else:
        text = formatting.as_list(
            formatting.Text(
                "Так как эту игру выбил ты,",
                "то тебе остается только оценить сложность",
            ),
            formatting.Text("Оцените Сложность от 1 до 10.\n"),
            formatting.Italic("Если не знаете что поставить, то нажмите 'Пропустить'"),
        ).as_html()
        await callback_query.message.edit_text(
            text=text,
            reply_markup=build_difficulty_score_keyboard(callback_data),
        )


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.GAME_SCORED)
)
async def process_picture_score(
    callback_query: CallbackQuery, callback_data: GameSurveyCallbackData
) -> None:
    """Score Picture Callback."""

    await callback_query.answer()

    await callback_query.message.edit_text(
        text="Оцените Картинку от 1 до 10",
        reply_markup=build_picture_score_keyboard(callback_data),
    )


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.PICTURE_SCORED)
)
async def process_difficulty_score(
    callback_query: CallbackQuery, callback_data: GameSurveyCallbackData
) -> None:
    """Score Difficulty Callback."""

    await callback_query.answer()

    text = formatting.as_list(
        formatting.Text("Оцените Сложность от 1 до 10.\n"),
        formatting.Italic("Если не знаете что поставить, то нажмите 'Пропустить'"),
    ).as_html()

    await callback_query.message.edit_text(
        text=text, reply_markup=build_difficulty_score_keyboard(callback_data)
    )


@game_score_router.callback_query(
    GameSurveyCallbackData.filter(F.state == SurveyState.DIFFICULTY_SCORED)
)
async def process_result(
    callback_query: CallbackQuery,
    callback_data: GameSurveyCallbackData,
    request: Request,
) -> None:
    """Result Callback."""

    text = formatting.as_list(
        formatting.Text("Ваша оценка:\n"),
        formatting.Text(f"Игра: {callback_data.game_score}"),
        formatting.Text(f"Картинка: {callback_data.picture_score}"),
        formatting.Text(f"Сложность: {callback_data.difficulty_score}"),
    ).as_html()

    await callback_query.answer(
        text=text,
        show_alert=True,
    )

    await request.add_survey(
        game_score=callback_data.game_score,
        picture_score=callback_data.picture_score,
        difficulty_score=callback_data.difficulty_score,
        user_id=callback_data.user_id,
        trophie_id=callback_data.history_id
    )

    await callback_query.message.edit_text(
        text="Оценить заново",
        reply_markup=build_start_survey_keyboard(
            text="Изменить оценку", callback_data=callback_data
        ),
    )