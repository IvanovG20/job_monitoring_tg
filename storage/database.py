"""Async SQLite database layer using aiosqlite."""
import logging
from datetime import date

import aiosqlite

from config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source      TEXT NOT NULL,
                external_id TEXT NOT NULL,
                sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, external_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.execute("""
            INSERT OR IGNORE INTO bot_state (key, value)
            VALUES ('monitoring_enabled', 'true')
        """)
        await db.commit()
    logger.info("Database initialised at %s", DB_PATH)


async def is_seen(source: str, external_id: str) -> bool:
    """Return True if the job was already sent to the user."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM seen_jobs WHERE source = ? AND external_id = ?",
            (source, external_id),
        )
        return await cursor.fetchone() is not None


async def mark_seen(source: str, external_id: str) -> None:
    """Record that the job has been sent to the user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO seen_jobs (source, external_id) VALUES (?, ?)",
            (source, external_id),
        )
        await db.commit()


async def get_state(key: str) -> str | None:
    """Retrieve a value from bot_state by key."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM bot_state WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_state(key: str, value: str) -> None:
    """Insert or update a key-value pair in bot_state."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()


async def get_stats_today() -> int:
    """Return number of jobs sent today."""
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM seen_jobs WHERE DATE(sent_at) = ?", (today,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
