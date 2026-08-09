"""Tests for :class:`src.scheduler.scheduler.Scheduler` job management.

The APScheduler instance is real but never started: ``add_job`` keeps the job
pending and ``get_job`` still finds it, which is enough to observe the trigger
that was built — and building the trigger is exactly where a missing interval
used to blow up.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.scheduler.scheduler import DEFAULT_DELTA, Scheduler

CHAT_ID = -1001234567890

# change_avatar is called with exactly these four arguments; APScheduler
# validates the signature when the job is created, but never calls it here.
BOT = object()
REQUEST = object()


@pytest.fixture(name="scheduler")
def scheduler_fixture():
    """A Scheduler over a real, never started, AsyncIOScheduler."""

    return Scheduler(AsyncIOScheduler(timezone=pytz.utc))


def get_trigger(scheduler: Scheduler):
    """Return the interval trigger of the chat's job."""

    job = scheduler.scheduler.get_job(str(CHAT_ID))
    assert job is not None, "no job was scheduled for the chat"
    return job.trigger


async def test_set_date_creates_missing_job(scheduler):
    """A known chat without a job must not crash on /set_date.

    The job is missing whenever start() skipped the chat because the bot was
    not a member at boot. /set_date passes no delta, and the interval used to
    be handed to the trigger as None.
    """

    scheduler.where_run[CHAT_ID] = {
        "date": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "delta": 7,
    }
    date = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, date=date)

    trigger = get_trigger(scheduler)
    assert trigger.interval == timedelta(days=7), "stored interval was dropped"
    assert trigger.start_date == date
    assert scheduler.where_run[CHAT_ID] == {"date": date, "delta": 7}


async def test_set_delta_creates_missing_job(scheduler):
    """The mirror case: /set_delta passes no date, so the stored one is used."""

    date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    scheduler.where_run[CHAT_ID] = {"date": date, "delta": 7}

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, delta=3)

    trigger = get_trigger(scheduler)
    assert trigger.interval == timedelta(days=3)
    assert trigger.start_date == date, "stored date was dropped"
    assert scheduler.where_run[CHAT_ID] == {"date": date, "delta": 3}


async def test_unknown_chat_falls_back_to_default_delta(scheduler):
    """With nothing stored for the chat, the interval falls back instead of None."""

    date = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, date=date)

    assert get_trigger(scheduler).interval == timedelta(days=DEFAULT_DELTA)
    assert scheduler.where_run[CHAT_ID] == {"date": date, "delta": DEFAULT_DELTA}


async def test_unknown_chat_falls_back_to_now(scheduler):
    """With no date either, the rotation starts from now rather than from None."""

    before = datetime.now(timezone.utc)

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, delta=5)

    trigger = get_trigger(scheduler)
    assert trigger.interval == timedelta(days=5)
    assert before <= trigger.start_date <= datetime.now(timezone.utc)


async def test_where_run_never_holds_none(scheduler):
    """change_avatar adds where_run['delta'] to where_run['date'] unguarded.

    Either of them being None turns every single rotation into a TypeError, so
    no call may leave a partially filled entry behind.
    """

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID)

    entry = scheduler.where_run[CHAT_ID]
    assert entry["date"] is not None
    assert entry["delta"] is not None
    # The arithmetic change_avatar performs after a successful rotation.
    assert entry["date"] + timedelta(days=entry["delta"]) > entry["date"]


async def test_existing_job_is_rescheduled_not_duplicated(scheduler):
    """A second call reschedules the same job and merges the new value in."""

    date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, date=date, delta=7)

    await scheduler.add_change_avatar_job(BOT, REQUEST, CHAT_ID, delta=2)

    assert len(scheduler.scheduler.get_jobs()) == 1
    trigger = get_trigger(scheduler)
    assert trigger.interval == timedelta(days=2)
    assert trigger.start_date == date
    assert scheduler.where_run[CHAT_ID] == {"date": date, "delta": 2}
