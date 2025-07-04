import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from tracker import CoinTracker
from signal_generator import generate_signal
from config import TELEGRAM_TOKEN, USER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot, USER_ID)

signal_index = 0
cached_signals = []

main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("📈 Получить ещё сигнал")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    await message.answer("Добро пожаловать! Я AnSam Bot. Я дам тебе сигнал на монету, которая с высокой вероятностью даст +5% в течение суток.")

@dp.message_handler(lambda message: message.text == "📈 Получить ещё сигнал")
async def handle_signal_request(message: types.Message):
    global cached_signals, signal_index
    if message.from_user.id != USER_ID:
        return

    if not cached_signals:
        cached_signals = generate_signal(top_n=3)
        signal_index = 0

    if not cached_signals:
        await message.answer("⚠️ Сейчас нет подходящих монет для сигнала. Попробуй позже.")
        return

    result = cached_signals[signal_index % len(cached_signals)]
    signal_index += 1

    text = (
        f"💡 *Сигнал на рост: {result['name']}*
"
        f"Цена входа: `{result['price']} USD`
"
        f"Цель: `{result['target_price']} USD` (+5%)
"
        f"Стоп-лосс: `{result['stop_loss']} USD`
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"RSI: {result['rsi']}, MA7: {result['ma7']}, MA20: {result['ma20']}, 24ч изм: {result['change_24h']}%"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['id']}_{result['price']}")
    )

    await message.answer(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def handle_track_coin(callback_query: types.CallbackQuery):
    _, coin_id, price = callback_query.data.split("_")
    await bot.answer_callback_query(callback_query.id)
    await tracker.track_coin(coin_id, float(price))
    await bot.send_message(USER_ID, f"🔔 Отслеживание *{coin_id}* запущено. Уведомлю при росте на +3.5% или +5%.", parse_mode="Markdown")

async def send_daily_signal():
    global cached_signals, signal_index
    cached_signals = generate_signal(top_n=3)
    signal_index = 0
    if not cached_signals:
        await bot.send_message(USER_ID, "⚠️ Сейчас нет подходящих монет для сигнала. Попробуй позже.")
        return

    result = cached_signals[signal_index % len(cached_signals)]
    signal_index += 1

    text = (
        f"💡 *Сигнал на рост: {result['name']}*
"
        f"Цена входа: `{result['price']} USD`
"
        f"Цель: `{result['target_price']} USD` (+5%)
"
        f"Стоп-лосс: `{result['stop_loss']} USD`
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"RSI: {result['rsi']}, MA7: {result['ma7']}, MA20: {result['ma20']}, 24ч изм: {result['change_24h']}%"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['id']}_{result['price']}")
    )

    await bot.send_message(USER_ID, text, reply_markup=keyboard)

async def on_startup(dp):
    logger.info("⏳ До следующего сигнала: 1167.0 минут")
    scheduler.add_job(send_daily_signal, "interval", minutes=1167)
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
