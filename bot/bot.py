import os
import aiohttp
import asyncpg
import redis
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from telethon import TelegramClient

# Загружаем переменные окружения из .env
load_dotenv()

# Инициируем подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

class ChannelManager:
    def __init__(self):
        self.pool = None
        self.client = None

    async def init_db(self):
        """
        Инициализация пула соединений к Postgres и создание таблицы (если не существует).
        """
        self.pool = await asyncpg.create_pool(
            user='bot_user',
            password='bot_password',
            database='telegram_bot',
            host='postgres'
        )
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    user_id TEXT,
                    channel_name TEXT,
                    PRIMARY KEY (user_id, channel_name)
                )
            ''')

    async def add_channel(self, user_id: str, channel: str):
        """
        Добавить канал в БД (ON CONFLICT DO NOTHING — чтобы не дублировать).
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO channels (user_id, channel_name) VALUES ($1, $2) ON CONFLICT DO NOTHING',
                user_id, channel
            )

    async def remove_channel(self, user_id: str, channel: str) -> bool:
        """
        Удалить канал из БД. Возвращает True, если что-то было удалено.
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM channels WHERE user_id = $1 AND channel_name = $2',
                user_id, channel
            )
            return result != 'DELETE 0'

    async def get_channels(self, user_id: str):
        """
        Получить список каналов для данного user_id.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT channel_name FROM channels WHERE user_id = $1',
                user_id
            )
            return [row['channel_name'] for row in rows]

    async def init_client(self):
        """
        Инициализировать Telethon-клиент.
        """
        if not self.client:
            self.client = TelegramClient(
                'bot_session',
                os.getenv('TELEGRAM_API_ID'),
                os.getenv('TELEGRAM_API_HASH')
            )
            await self.client.start(bot_token=os.getenv("TELEGRAM_BOT_TOKEN"))

    async def get_channel_messages(self, channel: str, limit: int = 10):
        """
        Получить последние N сообщений из канала/чата.
        """
        if not self.client:
            await self.init_client()

        try:
            entity = await self.client.get_entity(channel)
            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text:
                    messages.append(message.text)
            return messages
        except Exception as e:
            print(f"Error fetching messages from {channel}: {e}")
            return []

# Инициализируем менеджер каналов
channel_manager = ChannelManager()

async def get_summary(text: str) -> str:
    """
    Обращаемся к нашему микросервису summarizer, который крутится в отдельном контейнере.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://summarizer:8000/summarize', json={'text': text}) as response:
                result = await response.json()
                return result['summary']
    except Exception as e:
        print(f"Error getting summary: {e}")
        return "Error generating summary"

# Команды бота:

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to Channel Summarizer Bot! 📚\n\n"
        "Commands:\n"
        "/add_channel <channel_username> - Add a channel to monitor\n"
        "/list_channels - List monitored channels\n"
        "/remove_channel <channel_username> - Remove a channel\n"
        "/get_summary - Get today's summary of all channels"
    )
    await update.message.reply_text(welcome_message)

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide a channel username. Usage: /add_channel <channel_username>"
        )
        return

    channel = context.args[0]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    user_id = str(update.effective_user.id)
    await channel_manager.add_channel(user_id, channel)
    await update.message.reply_text(f"Channel {channel} added successfully!")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    channels = await channel_manager.get_channels(user_id)

    if not channels:
        await update.message.reply_text("No channels are currently being monitored.")
        return

    channel_list = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(channels))
    await update.message.reply_text(f"Monitored channels:\n{channel_list}")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide a channel username. Usage: /remove_channel <channel_username>"
        )
        return

    channel = context.args[0]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    user_id = str(update.effective_user.id)
    if await channel_manager.remove_channel(user_id, channel):
        await update.message.reply_text(f"Channel {channel} removed successfully!")
    else:
        await update.message.reply_text("Channel not found in the monitored list.")

async def get_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    channels = await channel_manager.get_channels(user_id)

    if not channels:
        await update.message.reply_text(
            "No channels are being monitored. Add channels using /add_channel command."
        )
        return

    await update.message.reply_text("Fetching and summarizing channel messages... This may take a moment.")

    try:
        summaries = []
        for channel in channels:
            cache_key = f"summary:{channel}"
            cached_summary = redis_client.get(cache_key)

            if cached_summary:
                # Если есть готовый кэш, берём из кэша
                summaries.append(f"{channel}:\n{cached_summary.decode()}")
                continue

            # Иначе — берём из Telethon
            messages = await channel_manager.get_channel_messages(channel)
            if messages:
                combined_text = "\n".join(messages)
                summary = await get_summary(combined_text)
                # Кладём результат в кэш на 24 часа
                redis_client.setex(cache_key, 86400, summary)
                summaries.append(f"{channel}:\n{summary}")
            else:
                summaries.append(f"{channel}:\nNo recent messages found.")

        await update.message.reply_text("Today's Channel Summaries:\n\n" + "\n\n".join(summaries))
    except Exception as e:
        print(f"Error generating summaries: {e}")
        await update.message.reply_text(
            "An error occurred while generating summaries. Please try again later."
        )

def main():
    import asyncio
    loop = asyncio.get_event_loop()
    # Подключаемся к БД до запуска бота
    loop.run_until_complete(channel_manager.init_db())

    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("list_channels", list_channels))
    application.add_handler(CommandHandler("remove_channel", remove_channel))
    application.add_handler(CommandHandler("get_summary", get_summary_command))

    application.run_polling()

if __name__ == "__main__":
    main()
