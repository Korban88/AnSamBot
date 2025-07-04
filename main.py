import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from signal_generator import generate_signal
from tracker import CoinTracker
from config import BOT_TOKEN, USER_ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot, USER_ID)

# Главные кнопки панели
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("📈 Прислать ещё сигнал")

# Обработчик кнопки Старт
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if message.chat.id != USER_ID:
        return
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard)

# Обработчик кнопки "Прислать ещё сигнал"
@dp.message_handler(lambda message: message.text == "📈 Прислать ещё сигнал")
async def handle_more_signal(message: types.Message):
    if message.chat.id != USER_ID:
        return
    logging.info("🔘 Запрос сигнала пользователем.")
    result = generate_signal()
    if not result:
        await message.answer("⚠️ Не удалось найти подходящую монету.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n"
        f"Цена входа: `{result['entry_price']}`\n"
        f"Цель: `{result['target_price']}` (+5%)\n"
        f"Стоп-лосс: `{result['stop_loss']}`\n"
        f"Вероятность роста: *{result['probability']}%*\n"
        f"_24ч: {result['change_24h']}% | RSI: {result['rsi']} | MA7: {result['ma7']} | MA20: {result['ma20']}_"
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await bot.send_message(USER_ID, text, reply_markup=keyboard)

# Обработка кнопки "Следить за монетой"
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track_"))
async def handle_track_button(callback_query: types.CallbackQuery):
    coin_symbol = callback_query.data.split("_", 1)[1]
    logging.info(f"🟡 Нажата кнопка отслеживания монеты: {coin_symbol}")
    await tracker.track_coin(coin_symbol)
    await bot.answer_callback_query(callback_query.id, text=f"Монета {coin_symbol} добавлена к отслеживанию!")

# Отправка сигнала каждый день в 8:00
async def send_daily_signal():
    logging.info("⏰ Автоматическая отправка сигнала в 8:00")
    result = generate_signal()
    if not result:
        await bot.send_message(USER_ID, "⚠️ Не удалось найти подходящую монету.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n"
        f"Цена входа: `{result['entry_price']}`\n"
        f"Цель: `{result['target_price']}` (+5%)\n"
        f"Стоп-лосс: `{result['stop_loss']}`\n"
        f"Вероятность роста: *{result['probability']}%*\n"
        f"_24ч: {result['change_24h']}% | RSI: {result['rsi']} | MA7: {result['ma7']} | MA20: {result['ma20']}_"
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await bot.send_message(USER_ID, text, reply_markup=keyboard)

async def on_startup(dp):
    scheduler.add_job(send_daily_signal, trigger='cron', hour=8, minute=0)
    scheduler.start()
    logging.info("⏳ До следующего сигнала: 1167.0 минут")

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "Bot is running!"

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
