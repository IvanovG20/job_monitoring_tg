"""hh.ru vacancy parser via public RSS feed (no auth required)."""
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp

from config import HH_HEADERS, HH_RSS_PARAMS, HH_RSS_URL
from storage.database import is_seen, mark_seen

logger = logging.getLogger(__name__)

_NS = {
    "hh": "https://hh.ru/info/1.0",
    "atom": "http://www.w3.org/2005/Atom",
}


def _extract_vacancy_id(url: str) -> str | None:
    """Extract vacancy ID from hh.ru URL like /vacancy/12345678."""
    match = re.search(r"/vacancy/(\d+)", url)
    return match.group(1) if match else None


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in special else ch for ch in text)


def _parse_items(xml_text: str) -> list[dict[str, Any]]:
    """Parse RSS XML and return list of vacancy dicts."""
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    vacancies = []
    for item in channel.findall("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        vacancy_id = _extract_vacancy_id(link)
        if not vacancy_id:
            continue

        # title format: "Вакансия — Работодатель, Город"
        parts = title.split(" — ", 1)
        name = parts[0].strip() if parts else title
        employer_city = parts[1].strip() if len(parts) > 1 else ""

        vacancies.append({
            "id": vacancy_id,
            "name": name,
            "employer_city": employer_city,
            "url": link,
            "pub_date": pub_date,
        })
    return vacancies


def _format_vacancy(v: dict[str, Any]) -> str:
    """Render a vacancy dict as a MarkdownV2 message."""
    name = _escape_md(v["name"])
    employer_city = _escape_md(v["employer_city"])
    url = v["url"]

    return (
        f"💼 *{name}*\n"
        f"🏢 {employer_city}\n"
        f"🔗 [Открыть на hh\\.ru]({url})\n"
        "📌 Источник: hh\\.ru"
    )


async def fetch_new_vacancies(session: aiohttp.ClientSession) -> list[str]:
    """Fetch hh.ru RSS and return formatted messages for unseen vacancies."""
    logger.info("hh.ru: starting vacancy check via RSS")
    try:
        async with session.get(
            HH_RSS_URL, params=HH_RSS_PARAMS, headers=HH_HEADERS
        ) as response:
            response.raise_for_status()
            xml_text = await response.text()
    except Exception as exc:
        logger.error("hh.ru RSS request failed: %s", exc)
        return []

    items = _parse_items(xml_text)
    logger.info("hh.ru: received %d vacancies from RSS", len(items))

    messages: list[str] = []
    for vacancy in items:
        external_id = vacancy["id"]
        if await is_seen("hh", external_id):
            continue
        await mark_seen("hh", external_id)
        messages.append(_format_vacancy(vacancy))
        logger.info("hh.ru: new vacancy queued — %s", vacancy["name"])

    return messages
