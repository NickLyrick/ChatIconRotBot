from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler

    async def add_job(self, func, bot, request, chat_id, date, delta):
        job = self.scheduler.get_job(str(chat_id))

        if job is None:
            self.scheduler.add_job(func=func,
                                   trigger="interval",
                                   days=1,
                                   start_date=date,
                                   id=str(chat_id),
                                   args=[bot, request, chat_id])
        else:
            where_run = await request.get_chats()
            if date is None:
                date = where_run[chat_id]['date']
            if delta is None:
                delta = where_run[chat_id]['delta']

            job.reschedule(trigger='interval', days=delta, start_date=date)
            job.modify(args=[bot, request, chat_id])
