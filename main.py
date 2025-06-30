import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keep_alive import keep_alive
from utils import get_daily_crypto_signal

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start с кнопками
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Получить ещё сигнал"))
    keyboard.add(types.KeyboardButton("Сообщить об ошибке"))
    await message.answer("Бот работает и готов присылать крипто-сигналы.", reply_markup=keyboard)

# Обработка кнопки «Получить ещё сигнал»
@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_extra_signal(message: types.Message):
    signal = get_daily_crypto_signal()
    await message.answer(f"Дополнительный сигнал: {signal}")

# Обработка кнопки «Сообщить об ошибке»
@dp.message_handler(lambda message: message.text == "Сообщить об ошибке")
async def handle_report(message: types.Message):
    await message.answer("Спасибо, мы проверим. Ошибка будет зафиксирована.")

# Планировщик — ежедневная отправка сигнала
async def send_daily_signal():
    signal = get_daily_crypto_signal()
    if CHAT_ID:
        await bot.send_message(chat_id=CHAT_ID, text=f"Ежедневный сигнал: {signal}")
    else:
        logger.warning("CHAT_ID не установлен!")

# Запуск планировщика
async def on_startup(dispatcher):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
    scheduler.start()
    logger.info("Бот запущен и готов к работе.")

if __name__ == "__main__":
    keep_alive()  # Railway uptime
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
