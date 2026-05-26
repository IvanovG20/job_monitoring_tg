"""Telegram channel parser using Telethon."""
import logging

from telethon import TelegramClient
from telethon.tl.types import Message

from config import KEYWORDS, TG_CHANNELS
from storage.database import is_seen, mark_seen

logger = logging.getLogger(__name__)

_MESSAGES_LIMIT = 10
_TEXT_MAX_LEN = 800


def _matches_keywords(text: str) -> bool:
    """Return True if the text contains at least one keyword."""
    lower = text.lower()
    return any(kw in lower for kw in KEYWORDS)


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in special else ch for ch in text)


def _build_message_url(channel: str, message_id: int) -> str:
    """Construct a t.me link for the given channel and message."""
    username = channel.lstrip("@")
    return f"https://t.me/{username}/{message_id}"


def _format_post(channel: str, message: Message) -> str:
    """Render a Telegram post as a MarkdownV2 message."""
    raw_text: str = message.text or message.message or ""
    excerpt = _escape_md(raw_text[:_TEXT_MAX_LEN])
    if len(raw_text) > _TEXT_MAX_LEN:
        excerpt += "\\.\\.\\."
    url = _build_message_url(channel, message.id)
    channel_escaped = _escape_md(channel)

    return (
        f"📢 *Вакансия из канала {channel_escaped}*\n\n"
        f"{excerpt}\n\n"
        f"🔗 [Открыть сообщение]({url})\n"
        "📌 Источник: Telegram"
    )


async def fetch_new_posts(client: TelegramClient) -> list[str]:
    """Scan configured channels and return messages for unseen relevant posts."""
    logger.info("Telegram channels: starting check (%d channels)", len(TG_CHANNELS))
    messages: list[str] = []

    for channel in TG_CHANNELS:
        try:
            async for msg in client.iter_messages(channel, limit=_MESSAGES_LIMIT):
                if not isinstance(msg, Message):
                    continue
                text = msg.text or msg.message or ""
                if not text or not _matches_keywords(text):
                    continue

                external_id = f"{channel}_{msg.id}"
                if await is_seen("telegram", external_id):
                    continue

                await mark_seen("telegram", external_id)
                messages.append(_format_post(channel, msg))
                logger.info("Telegram: new post queued from %s (id=%d)", channel, msg.id)

        except Exception as exc:
            logger.error("Failed to read channel %s: %s", channel, exc)

    logger.info("Telegram channels: %d new posts found", len(messages))
    return messages
