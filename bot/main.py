"""Entry point: initialise bot, scheduler, and shared clients."""
import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient

from bot.handlers import router
from bot.notifier import send_to_owner
from config import (
    BOT_TOKEN,
    HH_CHECK_INTERVAL_MINUTES,
    SESSION_PATH,
    TG_API_HASH,
    TG_API_ID,
    TG_CHECK_INTERVAL_MINUTES,
    TIMEZONE,
)
from parsers.hh import fetch_new_vacancies
from parsers.tg_channels import fetch_new_posts
from storage.database import get_state, init_db

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


async def check_tg_channels(bot: Bot, tg_client: TelegramClient) -> None:
    """Scheduled job: fetch new Telegram channel posts and notify the owner."""
    if await get_state("monitoring_enabled") != "true":
        logger.info("Telegram channels check skipped (monitoring paused)")
        return
    messages = await fetch_new_posts(tg_client)
    for text in messages:
        await send_to_owner(bot, text)


async def main() -> None:
    """Bootstrap all services and start polling."""
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    tg_client = TelegramClient(SESSION_PATH, TG_API_ID, TG_API_HASH)
    await tg_client.start()
    logger.info("Telethon client connected")

    async with aiohttp.ClientSession() as http_session:
        scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        scheduler.add_job(
            check_hh,
            "interval",
            minutes=HH_CHECK_INTERVAL_MINUTES,
            kwargs={"bot": bot, "session": http_session},
        )
        scheduler.add_job(
            check_tg_channels,
            "interval",
            minutes=TG_CHECK_INTERVAL_MINUTES,
            kwargs={"bot": bot, "tg_client": tg_client},
        )
        scheduler.start()
        logger.info(
            "Scheduler started (hh=%dm, tg=%dm)",
            HH_CHECK_INTERVAL_MINUTES,
            TG_CHECK_INTERVAL_MINUTES,
        )

        try:
            await dp.start_polling(bot)
        finally:
            scheduler.shutdown(wait=False)
            await tg_client.disconnect()
            logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
