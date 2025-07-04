import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from config import BOT_TOKEN, USER_ID
from signal_generator import generate_signal
from tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
tracker = CoinTracker(bot, USER_ID)

# Главное меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("📈 Получить ещё сигнал"))
main_keyboard.add(KeyboardButton("🛑 Остановить все отслеживания"))

# Команда старт
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard)

# Обработка команды получения сигнала
@dp.message_handler(lambda message: message.text == "📈 Получить ещё сигнал")
async def send_signal(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    result = generate_signal()
    if not result:
        await message.answer("⚠️ Не удалось найти перспективную монету для сигнала.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"Текущая цена: `{result['price']}`\n"
        f"Цель: `{result['target_price']} (+5%)`\n"
        f"Stop-loss: `{result['stop_loss']}`\n\n"
        f"*Вероятность роста:* {result['probability']}%\n"
        f"📊 {result['reason']}"
    )

    track_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track:{result['symbol']}")
    )
    await message.answer(text, reply_markup=track_button)

# Обработка кнопки "Остановить все отслеживания"
@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    await tracker.stop_all()
    await message.answer("⛔️ Все отслеживания монет остановлены.")

# Обработка inline-кнопки "Следить за монетой"
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def handle_tracking_callback(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split(":")[1]
    await tracker.start_tracking(symbol)
    await callback_query.answer(f"⏱ Начинаем отслеживать {symbol}")

# Плановая рассылка сигнала каждый день в 8:00
async def send_daily_signal():
    result = generate_signal()
    if not result:
        await bot.send_message(USER_ID, "⚠️ Не удалось найти монету для сигнала.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"Текущая цена: `{result['price']}`\n"
        f"Цель: `{result['target_price']} (+5%)`\n"
        f"Stop-loss: `{result['stop_loss']}`\n\n"
        f"*Вероятность роста:* {result['probability']}%\n"
        f"📊 {result['reason']}"
    )

    track_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track:{result['symbol']}")
    )
    await bot.send_message(USER_ID, text, reply_markup=track_button)

# Планировщик
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0)
scheduler.start()
logger.info("⏳ До следующего сигнала: 1167.0 минут")

# Запуск бота
async def on_startup(dp):
    logger.info("✅ Бот готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
