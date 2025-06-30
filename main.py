import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keep_alive import keep_alive
from utils import get_crypto_signal

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токены и ID из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please set it in Railway Variables.")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

# Планировщик задач
scheduler = AsyncIOScheduler()

# Отправка сигнала каждый день в 8:00
async def send_daily_signal():
    signal = await get_crypto_signal()
    await bot.send_message(chat_id=OWNER_ID, text=f"📈 Утренний сигнал:\n\n{signal}")

# Команда /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот работает и готов присылать крипто-сигналы.")

# Кнопка "Получить ещё сигнал"
@dp.message_handler(lambda message: message.text.lower() == "получить ещё сигнал")
async def more_signal_handler(message: types.Message):
    signal = await get_crypto_signal()
    await message.answer(f"📊 Новый сигнал:\n\n{signal}")

async def on_startup(_):
    logger.info("Бот запущен и готов к работе.")
    scheduler.add_job(send_daily_signal, trigger='cron', hour=8, minute=0)
    scheduler.start()

if __name__ == '__main__':
    keep_alive()  # Запускаем веб-сервер, чтобы Railway не засыпал
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
