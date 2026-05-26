"""Telegram bot command handlers."""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import HH_CHECK_INTERVAL_MINUTES, MY_TELEGRAM_ID, TG_CHECK_INTERVAL_MINUTES
from storage.database import get_state, get_stats_today, set_state

logger = logging.getLogger(__name__)
router = Router()


def _owner_only(message: Message) -> bool:
    """Return True if the message comes from the bot owner."""
    return message.from_user is not None and message.from_user.id == MY_TELEGRAM_ID


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Enable monitoring and greet the owner."""
    if not _owner_only(message):
        return
    await set_state("monitoring_enabled", "true")
    logger.info("Monitoring enabled via /start")
    await message.answer(
        "✅ Мониторинг вакансий запущен\\!\n\n"
        "Буду присылать новые Python-вакансии с hh\\.ru и Telegram\\-каналов\\.\n\n"
        "/pause — приостановить\n"
        "/resume — возобновить\n"
        "/status — текущий статус",
        parse_mode="MarkdownV2",
    )


@router.message(Command("pause"))
async def cmd_pause(message: Message) -> None:
    """Pause vacancy monitoring."""
    if not _owner_only(message):
        return
    await set_state("monitoring_enabled", "false")
    logger.info("Monitoring paused via /pause")
    await message.answer("⏸ Мониторинг приостановлен\\. Используй /resume для возобновления\\.", parse_mode="MarkdownV2")


@router.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
    """Resume vacancy monitoring."""
    if not _owner_only(message):
        return
    await set_state("monitoring_enabled", "true")
    logger.info("Monitoring resumed via /resume")
    await message.answer("▶️ Мониторинг возобновлён\\!", parse_mode="MarkdownV2")


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Show current monitoring status and today's stats."""
    if not _owner_only(message):
        return
    enabled = await get_state("monitoring_enabled")
    count = await get_stats_today()
    status_icon = "✅ Активен" if enabled == "true" else "⏸ Пауза"
    await message.answer(
        f"📊 Статус: {status_icon}\n"
        f"📨 Вакансий сегодня: {count}\n"
        f"⏱ hh\\.ru: каждые {HH_CHECK_INTERVAL_MINUTES} минут\n"
        f"⏱ Telegram\\-каналы: каждые {TG_CHECK_INTERVAL_MINUTES} минут",
        parse_mode="MarkdownV2",
    )
