# Telegram Channel Summarizer Bot

Небольшое микросервисное приложение, позволяющее получать краткие сводки (summary) последних сообщений из Telegram-каналов по запросу в боте.

---

## Основные возможности

- **Добавление/удаление** каналов к личному списку отслеживаемых (`/add_channel`, `/remove_channel`).
- **Просмотр** списка отслеживаемых каналов (`/list_channels`).
- **Получение суммаризации** последних сообщений по всем отслеживаемым каналам (`/get_summary`).
- **Кэширование** результатов суммаризации (Redis).
- **Хранение** списка каналов в базе данных (Postgres).

---

## Технологии и компоненты

- **Python Telegram Bot** и **Telethon** для взаимодействия с Telegram.
- **FastAPI** + **Transformers** (BART) для микросервиса суммаризации.
- **Postgres** для хранения данных о каналах.
- **Redis** для кэширования суммаризаций.
- **Docker Compose** для сборки и запуска всех сервисов.

---

## Структура проекта

```bash
.
├── bot/
│   ├── bot.py             # Исходный код Telegram-бота
│   ├── Dockerfile         # Dockerfile для бота
│   └── requirements.txt   # Python-зависимости для бота
├── summarizer/
│   ├── summarizer.py      # Код FastAPI-сервиса для суммаризации
│   ├── Dockerfile         # Dockerfile для summarizer
│   └── requirements.txt   # Python-зависимости для summarizer
├── docker-compose.yml      # docker-compose для запуска проекта
├── .env                    # Файл с переменными окружения (не класть в публичный репозиторий!)
└── README.md               # Текущее описание