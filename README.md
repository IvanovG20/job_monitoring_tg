# Job Monitor Bot

Telegram-бот, который мониторит вакансии Python-разработчика на **hh.ru** и в **Telegram-каналах** и мгновенно присылает новые в личку.

---

## Возможности

- Парсинг hh.ru каждые 10 минут через официальное API
- Парсинг Telegram-каналов каждые 5 минут через Telethon
- Дедупликация — одна вакансия приходит ровно один раз
- Управление мониторингом командами бота
- Статистика за день

---

## Получение токенов

### BOT_TOKEN
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`, следуйте инструкциям
3. Скопируйте выданный токен

### MY_TELEGRAM_ID
1. Напишите [@userinfobot](https://t.me/userinfobot)
2. Скопируйте числовой `Id`

### TG_API_ID и TG_API_HASH
1. Зайдите на [my.telegram.org](https://my.telegram.org)
2. Войдите через номер телефона → **API development tools**
3. Создайте приложение, скопируйте `api_id` и `api_hash`

---

## Запуск локально

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd job_monitoring_tg

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Заполнить .env своими значениями

# 5. Запустить бота
python -m bot.main
```

При первом запуске Telethon запросит номер телефона и код подтверждения — это одноразовая процедура; сессия сохранится в `data/telethon.session`.

---

## Запуск через Docker

```bash
# Настроить .env (см. выше)
cp .env.example .env

# Собрать и запустить
docker compose up -d --build

# Логи
docker compose logs -f bot
```

> **Внимание:** при первом запуске Docker-контейнер не сможет пройти аутентификацию Telethon интерактивно. Сначала запустите бота **локально** один раз, чтобы создать файл `data/telethon.session`, затем поднимайте Docker — сессия примонтируется через volume.

---

## Команды бота

| Команда   | Действие                                      |
|-----------|-----------------------------------------------|
| `/start`  | Включить мониторинг и получить приветствие    |
| `/pause`  | Приостановить мониторинг                      |
| `/resume` | Возобновить мониторинг                        |
| `/status` | Показать статус и статистику за сегодня       |

---

## Структура проекта

```
job_monitoring_tg/
├── bot/
│   ├── main.py          # точка входа, инициализация бота и планировщика
│   ├── handlers.py      # команды /start /pause /resume /status
│   └── notifier.py      # отправка сообщений владельцу
├── parsers/
│   ├── hh.py            # парсер hh.ru через aiohttp
│   └── tg_channels.py   # парсер каналов через Telethon
├── storage/
│   └── database.py      # aiosqlite: init_db, is_seen, mark_seen, get/set_state
├── config.py            # настройки и константы
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
