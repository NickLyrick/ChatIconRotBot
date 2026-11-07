"""Run the scheduled jobs that are due.

There is no in-process scheduler: the bot may sleep between updates, so an
external cron calls :func:`run_due_jobs` (through ``POST /jobs/tick``) and the
database alone decides what is due. Every job is claimed in the database before
it runs, so repeated or concurrent ticks never run the same job twice.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from aiogram import Bot
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.database.schemas import Chat
from src.scheduler.jobs import change_avatar, finish_survey
from src.utility.schedule import get_zone, localize

# Survey results are published on the 1st of every month at this hour (UTC).
SURVEY_HOUR_UTC = 12

# Only one tick at a time within the process; the database claims cover the rest.
_tick_lock = asyncio.Lock()


@dataclass
class TickReport:
    """What a tick did, returned to the caller of /jobs/tick."""

    rotations: list[int] = field(default_factory=list)
    surveys: list[int] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)


def next_rotation_date(
    scheduled: datetime, delta_days: int, now: datetime, zone: str = "UTC"
) -> datetime | None:
    """Return the date to move a due rotation to, or None if it is not due yet.

    After a long sleep several periods may have passed: the chat still gets a
    single rotation, and the schedule jumps to the first slot after ``now``
    while keeping the time of day in the chat's zone, across DST changes too.
    """

    if scheduled > now:
        return None

    step = timedelta(days=max(delta_days or 1, 1))
    local = scheduled.astimezone(get_zone(zone)).replace(tzinfo=None)
    # Counted in UTC the number of missed slots can be off by one around a DST
    # change, so start one slot early and step forward.
    slot = max((now - scheduled) // step, 1)
    while (candidate := localize(local + slot * step, zone)) <= now:
        slot += 1
    return candidate


def survey_period_due(now: datetime) -> date | None:
    """Return the month whose survey should be published by now, or None.

    The month is identified by its first day; the survey published in it covers
    the previous month.
    """

    month_start = now.date().replace(day=1)
    due_at = datetime(now.year, now.month, 1, SURVEY_HOUR_UTC, tzinfo=timezone.utc)
    return month_start if now >= due_at else None


async def _is_group_chat(bot: Bot, chat_id: int) -> bool:
    """Whether the bot is still in the chat and the chat is not private."""

    try:
        chat = await bot.get_chat(chat_id=chat_id)
    except Exception as e:
        logging.warning(f"{__name__}: cannot get chat {chat_id}, skipping it: {e}")
        return False
    return chat.type != "private"


async def _notify_admins(bot: Bot, chat_id: int, error: Exception) -> None:
    """Report an unexpected error to the bot admins."""

    text = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__} для чата {chat_id}:"),
        formatting.Pre(error),
    ).as_html()
    for admin_id in settings.bot.admin_ids:
        try:
            await bot.send_message(admin_id, text=text)
        except Exception:
            logging.exception(f"{__name__}: cannot notify admin {admin_id}")


async def _run_chat(
    bot: Bot, request: Request, chat: Chat, now: datetime, report: TickReport
) -> None:
    """Claim and run whatever is due for one chat."""

    period = survey_period_due(now)
    survey_due = period is not None and chat.survey_period != period
    new_date = next_rotation_date(chat.date, chat.delta, now, chat.timezone)

    if not survey_due and new_date is None:
        return

    # Claim before checking the chat: an unreachable chat is then skipped once
    # per period instead of on every tick.
    survey_claimed = survey_due and await request.claim_survey(chat.chat_id, period)
    rotation_claimed = new_date is not None and await request.claim_rotation(
        chat.chat_id, chat.date, new_date
    )

    if not (survey_claimed or rotation_claimed):
        return

    if not await _is_group_chat(bot, chat.chat_id):
        report.skipped.append(chat.chat_id)
        return

    if survey_claimed:
        await finish_survey(bot=bot, request=request, chat_id=chat.chat_id)
        report.surveys.append(chat.chat_id)

    if rotation_claimed:
        await change_avatar(bot=bot, request=request, chat_id=chat.chat_id)
        report.rotations.append(chat.chat_id)


async def run_due_jobs(bot: Bot, request: Request, now: datetime | None = None) -> TickReport:
    """Run every avatar rotation and survey that is due."""

    async with _tick_lock:
        now = now or datetime.now(timezone.utc)
        report = TickReport()

        for chat in await request.get_chats():
            try:
                await _run_chat(bot, request, chat, now, report)
            except Exception as e:
                logging.exception(f"{__name__}: tick failed for chat {chat.chat_id}")
                report.failed.append(chat.chat_id)
                await _notify_admins(bot, chat.chat_id, e)

        logging.info(f"{__name__}: tick done: {report}")
        return report
