"""Entry point: initialise bot, scheduler, and shared clients."""
import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.handlers import BOT_COMMANDS, router
from bot.notifier import send_to_owner
from config import BOT_TOKEN, HH_CHECK_INTERVAL_MINUTES, TIMEZONE
from parsers.hh import fetch_new_vacancies
from storage.database import cleanup_old_jobs, get_state, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def check_hh(bot: Bot, session: aiohttp.ClientSession) -> None:
    """Scheduled job: fetch new hh.ru vacancies and notify the owner."""
    if await get_state("monitoring_enabled") != "true":
        logger.info("hh.ru check skipped (monitoring paused)")
        return
    messages = await fetch_new_vacancies(session)
    for text in messages:
        await send_to_owner(bot, text)


async def main() -> None:
    """Bootstrap all services and start polling."""
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands(BOT_COMMANDS)

    dp = Dispatcher()
    dp.include_router(router)

    async with aiohttp.ClientSession() as http_session:
        scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        scheduler.add_job(
            check_hh,
            "interval",
            minutes=HH_CHECK_INTERVAL_MINUTES,
            kwargs={"bot": bot, "session": http_session},
        )
        scheduler.add_job(cleanup_old_jobs, "interval", hours=24)
        scheduler.start()
        logger.info("Scheduler started (hh=%dm)", HH_CHECK_INTERVAL_MINUTES)

        try:
            await dp.start_polling(bot)
        finally:
            scheduler.shutdown(wait=False)
            logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот выключен.")
