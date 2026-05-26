"""Utility for sending messages to the owner."""
import logging

from aiogram import Bot

from config import MY_TELEGRAM_ID

logger = logging.getLogger(__name__)


async def send_to_owner(bot: Bot, text: str) -> None:
    """Send a Markdown message to the bot owner.

    Silently logs errors instead of crashing the scheduler job.
    """
    try:
        await bot.send_message(
            chat_id=MY_TELEGRAM_ID,
            text=text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error("Failed to send message to owner: %s", exc)
