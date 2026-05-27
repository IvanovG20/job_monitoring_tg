"""Configuration and constants for the job monitoring bot."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
MY_TELEGRAM_ID: int = int(os.environ["MY_TELEGRAM_ID"])
# TG_API_ID: int = int(os.environ["TG_API_ID"])
# TG_API_HASH: str = os.environ["TG_API_HASH"]

DB_PATH: str = str(DATA_DIR / "jobs.db")
# SESSION_PATH: str = str(DATA_DIR / "telethon")

HH_CHECK_INTERVAL_MINUTES: int = 10
TG_CHECK_INTERVAL_MINUTES: int = 5

HH_RSS_URL: str = "https://hh.ru/search/vacancy/rss"
HH_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml",
}
HH_RSS_PARAMS: dict = {
    "text": "Python developer OR Python разработчик",
    "area": [1, 2],
    "experience": ["between1And3", "between3And6"],
    "schedule": ["remote", "flexible", "fullDay"],
    "order_by": "publication_time",
    "items_on_page": 20,
}

TG_CHANNELS: list[str] = [
    "@python_jobs",
    "@django_jobs",
    "@it_jobs_spb",
]

KEYWORDS: list[str] = ["python", "fastapi", "django", "backend", "бэкенд", "питон"]

TIMEZONE: str = "Europe/Moscow"
