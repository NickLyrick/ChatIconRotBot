"""Tests for :mod:`src.scheduler.runner`.

The runner decides from the database alone what is due, and claims every job
before running it. The date arithmetic is checked directly; the tick itself
runs against an in-memory stand-in for :class:`src.database.Request` whose
claims behave like the conditional UPDATEs they replace.
"""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.database.schemas import Chat
from src.scheduler import runner
from src.scheduler.runner import next_rotation_date, run_due_jobs, survey_period_due

UTC = timezone.utc
CHAT_ID = -1001234567890
OTHER_CHAT_ID = -1009876543210


# --- next_rotation_date -------------------------------------------------------


def test_rotation_in_the_future_is_not_due():
    now = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)

    assert next_rotation_date(now + timedelta(minutes=1), 1, now) is None


def test_rotation_due_exactly_now_moves_one_period():
    now = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)

    assert next_rotation_date(now, 7, now) == now + timedelta(days=7)


def test_missed_periods_collapse_into_one_rotation():
    """After a long sleep the schedule jumps past now, keeping the time of day."""

    scheduled = datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
    now = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)

    new_date = next_rotation_date(scheduled, 7, now)

    assert new_date == datetime(2026, 11, 5, 18, 0, tzinfo=UTC)
    assert new_date > now
    assert new_date - timedelta(days=7) <= now


def test_non_positive_interval_falls_back_to_one_day():
    now = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)

    assert next_rotation_date(now, 0, now) == now + timedelta(days=1)


def test_rotation_keeps_local_time_across_dst_end():
    """18:00 in Berlin stays 18:00 when summer time ends on 25 October."""

    scheduled = datetime(2026, 10, 24, 16, 0, tzinfo=UTC)  # 18:00 CEST

    new_date = next_rotation_date(scheduled, 1, scheduled, "Europe/Berlin")

    assert new_date == datetime(2026, 10, 25, 17, 0, tzinfo=UTC)  # 18:00 CET


def test_rotation_keeps_local_time_across_dst_start():
    scheduled = datetime(2026, 3, 28, 17, 0, tzinfo=UTC)  # 18:00 CET

    new_date = next_rotation_date(scheduled, 1, scheduled, "Europe/Berlin")

    assert new_date == datetime(2026, 3, 29, 16, 0, tzinfo=UTC)  # 18:00 CEST


@pytest.mark.parametrize(
    "now",
    [
        # Within the hour the DST change shifts the slot by: the next slot is
        # still 25.10 18:00 local (17:00 UTC), not a day later.
        datetime(2026, 10, 25, 16, 30, tzinfo=UTC),
        datetime(2026, 10, 25, 15, 59, tzinfo=UTC),
    ],
)
def test_missed_slots_across_dst_do_not_skip_a_slot(now):
    scheduled = datetime(2026, 10, 20, 16, 0, tzinfo=UTC)  # 18:00 CEST

    assert next_rotation_date(scheduled, 1, now, "Europe/Berlin") == datetime(
        2026, 10, 25, 17, 0, tzinfo=UTC
    )


def test_missed_slots_across_dst_land_on_the_first_slot_after_now():
    scheduled = datetime(2026, 10, 20, 16, 0, tzinfo=UTC)  # 18:00 CEST
    now = datetime(2026, 10, 25, 17, 30, tzinfo=UTC)  # just after 18:00 CET

    assert next_rotation_date(scheduled, 1, now, "Europe/Berlin") == datetime(
        2026, 10, 26, 17, 0, tzinfo=UTC
    )


def test_zone_without_dst_matches_plain_utc_steps():
    scheduled = datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
    now = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)

    for zone in ("UTC", "Europe/Moscow", "Asia/Vladivostok"):
        assert next_rotation_date(scheduled, 7, now, zone) == datetime(
            2026, 11, 5, 18, 0, tzinfo=UTC
        )


# --- survey_period_due --------------------------------------------------------


def test_survey_not_due_before_noon_on_the_first():
    assert survey_period_due(datetime(2026, 11, 1, 11, 59, tzinfo=UTC)) is None


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 11, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 11, 3, 0, 0, tzinfo=UTC),
        datetime(2026, 11, 30, 23, 59, tzinfo=UTC),
    ],
)
def test_survey_due_from_noon_on_the_first(now):
    assert survey_period_due(now) == date(2026, 11, 1)


def test_survey_period_in_january():
    assert survey_period_due(datetime(2027, 1, 1, 12, 0, tzinfo=UTC)) == date(2027, 1, 1)


# --- run_due_jobs -------------------------------------------------------------


class FakeRequest:
    """In-memory chats table with the same claim semantics as Request."""

    def __init__(self, *chats: Chat):
        self.chats = {chat.chat_id: chat for chat in chats}

    async def get_chats(self):
        # Copies, like rows read in a separate session.
        return [
            Chat(
                chat_id=c.chat_id,
                date=c.date,
                delta=c.delta,
                survey_period=c.survey_period,
                timezone=c.timezone,
            )
            for c in self.chats.values()
        ]

    async def claim_rotation(self, chat_id, old_date, new_date):
        chat = self.chats[chat_id]
        if chat.date != old_date:
            return False
        chat.date = new_date
        return True

    async def claim_survey(self, chat_id, period):
        chat = self.chats[chat_id]
        if chat.survey_period == period:
            return False
        chat.survey_period = period
        return True


class FakeBot:
    """Answers get_chat with a group, or fails for chats the bot left."""

    def __init__(self, private=(), gone=()):
        self.private = set(private)
        self.gone = set(gone)

    async def get_chat(self, chat_id):
        if chat_id in self.gone:
            raise RuntimeError("chat not found")
        return SimpleNamespace(type="private" if chat_id in self.private else "supergroup")

    async def send_message(self, *args, **kwargs):
        pass


@pytest.fixture(name="calls")
def calls_fixture(monkeypatch):
    """Replace the jobs with recorders."""

    calls = {"avatar": [], "survey": []}

    async def change_avatar(bot, request, chat_id):
        calls["avatar"].append(chat_id)

    async def finish_survey(bot, request, chat_id):
        calls["survey"].append(chat_id)

    monkeypatch.setattr(runner, "change_avatar", change_avatar)
    monkeypatch.setattr(runner, "finish_survey", finish_survey)
    return calls


# Mid-month, so only rotations are in play unless a test says otherwise.
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
SURVEY_DONE = date(2026, 11, 1)


def make_chat(
    chat_id=CHAT_ID,
    scheduled=NOW - timedelta(hours=1),
    delta=1,
    survey=SURVEY_DONE,
    zone="Europe/Moscow",
):
    return Chat(
        chat_id=chat_id, date=scheduled, delta=delta, survey_period=survey, timezone=zone
    )


async def test_tick_steps_in_the_chat_zone(calls):
    """A Berlin chat's 18:00 rotation stays at 18:00 local after DST ends."""

    scheduled = datetime(2026, 10, 24, 16, 0, tzinfo=UTC)  # 18:00 CEST
    request = FakeRequest(make_chat(scheduled=scheduled, zone="Europe/Berlin"))

    await run_due_jobs(FakeBot(), request, now=scheduled + timedelta(minutes=5))

    assert request.chats[CHAT_ID].date == datetime(2026, 10, 25, 17, 0, tzinfo=UTC)


async def test_due_rotation_runs_and_moves_the_date(calls):
    request = FakeRequest(make_chat(delta=3))

    report = await run_due_jobs(FakeBot(), request, now=NOW)

    assert calls["avatar"] == [CHAT_ID]
    assert report.rotations == [CHAT_ID]
    assert request.chats[CHAT_ID].date == NOW - timedelta(hours=1) + timedelta(days=3)


async def test_second_tick_does_not_rotate_again(calls):
    request = FakeRequest(make_chat())

    await run_due_jobs(FakeBot(), request, now=NOW)
    await run_due_jobs(FakeBot(), request, now=NOW + timedelta(minutes=5))

    assert calls["avatar"] == [CHAT_ID]


async def test_lost_claim_skips_the_rotation(calls):
    """Another tick (or /set_date) changed the date in between: hands off."""

    request = FakeRequest(make_chat())

    async def lose(*_):
        return False

    request.claim_rotation = lose

    report = await run_due_jobs(FakeBot(), request, now=NOW)

    assert not calls["avatar"]
    assert not report.rotations


async def test_rotation_not_due_does_nothing(calls):
    request = FakeRequest(make_chat(scheduled=NOW + timedelta(hours=1)))

    await run_due_jobs(FakeBot(), request, now=NOW)

    assert not calls["avatar"]
    assert request.chats[CHAT_ID].date == NOW + timedelta(hours=1)


@pytest.mark.parametrize("bot", [FakeBot(private={CHAT_ID}), FakeBot(gone={CHAT_ID})])
async def test_unreachable_chat_is_skipped_once_per_period(calls, bot):
    request = FakeRequest(make_chat())

    report = await run_due_jobs(bot, request, now=NOW)
    again = await run_due_jobs(bot, request, now=NOW + timedelta(minutes=5))

    assert not calls["avatar"]
    assert report.skipped == [CHAT_ID]
    assert not again.skipped, "the claim must stop it from being retried every tick"


async def test_survey_runs_once_per_month(calls):
    request = FakeRequest(make_chat(scheduled=NOW + timedelta(days=1), survey=date(2026, 10, 1)))

    await run_due_jobs(FakeBot(), request, now=NOW)
    await run_due_jobs(FakeBot(), request, now=NOW + timedelta(hours=1))

    assert calls["survey"] == [CHAT_ID]
    assert request.chats[CHAT_ID].survey_period == date(2026, 11, 1)


async def test_survey_for_new_chat_runs(calls):
    request = FakeRequest(make_chat(scheduled=NOW + timedelta(days=1), survey=None))

    await run_due_jobs(FakeBot(), request, now=NOW)

    assert calls["survey"] == [CHAT_ID]


async def test_survey_waits_for_noon_on_the_first(calls):
    first_morning = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
    request = FakeRequest(make_chat(scheduled=first_morning + timedelta(days=1)))

    await run_due_jobs(FakeBot(), request, now=first_morning)
    assert not calls["survey"]

    await run_due_jobs(FakeBot(), request, now=first_morning.replace(hour=12))
    assert calls["survey"] == [CHAT_ID]


async def test_failure_in_one_chat_does_not_stop_the_others(calls):
    request = FakeRequest(make_chat(), make_chat(chat_id=OTHER_CHAT_ID))
    original = request.claim_rotation

    async def flaky(chat_id, old_date, new_date):
        if chat_id == CHAT_ID:
            raise RuntimeError("database hiccup")
        return await original(chat_id, old_date, new_date)

    request.claim_rotation = flaky

    report = await run_due_jobs(FakeBot(), request, now=NOW)

    assert report.failed == [CHAT_ID]
    assert calls["avatar"] == [OTHER_CHAT_ID]
