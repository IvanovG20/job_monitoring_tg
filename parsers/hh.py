"""hh.ru vacancy parser using aiohttp."""
import logging
from typing import Any

import aiohttp

from config import HH_API_URL, HH_HEADERS, HH_PARAMS
from storage.database import is_seen, mark_seen

logger = logging.getLogger(__name__)


def _format_salary(vacancy: dict[str, Any]) -> str:
    """Build a human-readable salary string, or empty string if absent."""
    salary = vacancy.get("salary")
    if not salary:
        return ""
    currency_map = {"RUR": "₽", "USD": "$", "EUR": "€", "KZT": "₸"}
    currency = currency_map.get(salary.get("currency", ""), salary.get("currency", ""))
    from_val = salary.get("from")
    to_val = salary.get("to")
    if from_val and to_val:
        return f"💰 {from_val:,} – {to_val:,} {currency}".replace(",", " ")
    if from_val:
        return f"💰 от {from_val:,} {currency}".replace(",", " ")
    if to_val:
        return f"💰 до {to_val:,} {currency}".replace(",", " ")
    return ""


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in special else ch for ch in text)


def _format_vacancy(vacancy: dict[str, Any]) -> str:
    """Render a vacancy dict as a MarkdownV2 message."""
    name = _escape_md(vacancy.get("name", "—"))
    employer = _escape_md(vacancy.get("employer", {}).get("name", "—"))
    schedule = _escape_md(vacancy.get("schedule", {}).get("name", "—"))
    url = vacancy.get("alternate_url", "")
    salary_line = _format_salary(vacancy)

    lines = [
        f"💼 *{name}*",
        f"🏢 {employer}",
    ]
    if salary_line:
        lines.append(salary_line)
    lines += [
        f"📍 {schedule}",
        f"🔗 [Открыть на hh\\.ru]({url})",
        "📌 Источник: hh\\.ru",
    ]
    return "\n".join(lines)


async def fetch_new_vacancies(session: aiohttp.ClientSession) -> list[str]:
    """Fetch hh.ru vacancies and return formatted messages for unseen ones.

    Returns an empty list when the API is unavailable.
    """
    logger.info("hh.ru: starting vacancy check")
    try:
        async with session.get(
            HH_API_URL, params=HH_PARAMS, headers=HH_HEADERS
        ) as response:
            response.raise_for_status()
            data = await response.json()
    except Exception as exc:
        logger.error("hh.ru request failed: %s", exc)
        return []

    items: list[dict] = data.get("items", [])
    logger.info("hh.ru: received %d vacancies", len(items))

    messages: list[str] = []
    for vacancy in items:
        external_id = str(vacancy["id"])
        if await is_seen("hh", external_id):
            continue
        await mark_seen("hh", external_id)
        messages.append(_format_vacancy(vacancy))
        logger.info("hh.ru: new vacancy queued — %s", vacancy.get("name"))

    return messages
