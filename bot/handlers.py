"""Telegram bot command handlers."""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import HH_CHECK_INTERVAL_MINUTES, MY_TELEGRAM_ID
from storage.database import get_state, get_stats_today, reset_seen_jobs, set_state

logger = logging.getLogger(__name__)
router = Router()

BOT_COMMANDS = [
    BotCommand(command="start",  description="Запустить мониторинг"),
    BotCommand(command="pause",  description="Приостановить мониторинг"),
    BotCommand(command="resume", description="Возобновить мониторинг"),
    BotCommand(command="status", description="Текущий статус"),
    BotCommand(command="reset",  description="Сбросить историю вакансий"),
]


def _owner_only(user_id: int) -> bool:
    """Return True if the user is the bot owner."""
    return user_id == MY_TELEGRAM_ID


def _main_keyboard() -> InlineKeyboardMarkup:
    """Build the main inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏸ Пауза",       callback_data="pause"),
            InlineKeyboardButton(text="▶️ Возобновить", callback_data="resume"),
        ],
        [
            InlineKeyboardButton(text="📊 Статус",      callback_data="status"),
            InlineKeyboardButton(text="🗑 Сброс истории", callback_data="reset"),
        ],
    ])


# ── Commands ──────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Enable monitoring and show the main menu."""
    if not _owner_only(message.from_user.id):
        return
    await set_state("monitoring_enabled", "true")
    logger.info("Monitoring enabled via /start")
    await message.answer(
        "✅ *Мониторинг вакансий запущен\\!*\n\n"
        f"Проверяю hh\\.ru каждые {HH_CHECK_INTERVAL_MINUTES} минут и присылаю новые Python\\-вакансии\\.",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


@router.message(Command("pause"))
async def cmd_pause(message: Message) -> None:
    """Pause vacancy monitoring."""
    if not _owner_only(message.from_user.id):
        return
    await set_state("monitoring_enabled", "false")
    logger.info("Monitoring paused via /pause")
    await message.answer(
        "⏸ Мониторинг приостановлен\\.",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
    """Resume vacancy monitoring."""
    if not _owner_only(message.from_user.id):
        return
    await set_state("monitoring_enabled", "true")
    logger.info("Monitoring resumed via /resume")
    await message.answer(
        "▶️ Мониторинг возобновлён\\!",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Show current monitoring status and today's stats."""
    if not _owner_only(message.from_user.id):
        return
    await _send_status(message.answer)


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Clear seen_jobs history."""
    if not _owner_only(message.from_user.id):
        return
    await _do_reset(message.answer)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "pause")
async def cb_pause(callback: CallbackQuery) -> None:
    if not _owner_only(callback.from_user.id):
        return
    await set_state("monitoring_enabled", "false")
    logger.info("Monitoring paused via button")
    await callback.answer("Мониторинг приостановлен")
    await callback.message.edit_text(
        "⏸ Мониторинг приостановлен\\.",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


@router.callback_query(F.data == "resume")
async def cb_resume(callback: CallbackQuery) -> None:
    if not _owner_only(callback.from_user.id):
        return
    await set_state("monitoring_enabled", "true")
    logger.info("Monitoring resumed via button")
    await callback.answer("Мониторинг возобновлён")
    await callback.message.edit_text(
        "▶️ Мониторинг возобновлён\\!",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery) -> None:
    if not _owner_only(callback.from_user.id):
        return
    await callback.answer()
    await _send_status(callback.message.answer)


@router.callback_query(F.data == "reset")
async def cb_reset(callback: CallbackQuery) -> None:
    if not _owner_only(callback.from_user.id):
        return
    await callback.answer("История очищена")
    await _do_reset(callback.message.answer)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _send_status(answer_fn) -> None:
    """Send status message using the provided answer function."""
    enabled = await get_state("monitoring_enabled")
    count = await get_stats_today()
    status_icon = "✅ Активен" if enabled == "true" else "⏸ Пауза"
    await answer_fn(
        f"📊 *Статус:* {status_icon}\n"
        f"📨 Вакансий сегодня: {count}\n"
        f"⏱ hh\\.ru: каждые {HH_CHECK_INTERVAL_MINUTES} минут",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )


async def _do_reset(answer_fn) -> None:
    """Clear seen_jobs and report the result."""
    deleted = await reset_seen_jobs()
    logger.info("seen_jobs reset: %d records deleted", deleted)
    await answer_fn(
        f"🗑 История очищена\\: удалено *{deleted}* записей\\.",
        parse_mode="MarkdownV2",
        reply_markup=_main_keyboard(),
    )
