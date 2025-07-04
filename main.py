import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from threading import Thread
from analysis import analyze_coin
from crypto_utils import get_top_coins
from tracker import CoinTracker

# === Конфигурация ===
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
OWNER_ID = 347552741

# === Инициализация ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
tracker = CoinTracker(bot, OWNER_ID)

# === Flask (Railway Ping) ===
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    thread = Thread(target=run_web)
    thread.start()

# === Сигналы ===
async def send_signal():
    top_coins = get_top_coins()
    logging.info(f"🔍 Анализ {len(top_coins)} монет...")
    selected = []

    for coin in top_coins:
        result = analyze_coin(coin['id'])
        if result and result['probability'] >= 65:
            selected.append((coin, result))

    selected.sort(key=lambda x: x[1]['probability'], reverse=True)
    top_3 = selected[:3]

    if not top_3:
        await bot.send_message(OWNER_ID, "⚠️ Нет подходящих монет для сигнала.")
        return

    for coin, analysis in top_3:
        text = (
            f"🧠 <b>Сигнал:</b>\n"
            f"Монета: <code>{coin['id']}</code>\n"
            f"Цена: {coin['current_price']} $\n"
            f"Рост за 24ч: {coin['price_change_percentage_24h']:.2f}%\n"
            f"🟢 Вероятность роста: <b>{analysis['probability']}%</b>\n"
            f"🎯 Цель: {round(coin['current_price'] * 1.05, 6)} $ (+5%)\n"
            f"🛑 Стоп-лосс: {round(coin['current_price'] * 0.965, 6)} $ (-3.5%)"
        )
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{coin['id']}")
        )
        await bot.send_message(OWNER_ID, "⚙️ Обработка сигнала...")
        await bot.send_message(OWNER_ID, text, reply_markup=keyboard)

# === Планировщик ===
scheduler = AsyncIOScheduler()
scheduler.add_job(send_signal, "cron", hour=8, minute=0)

# === Хендлеры ===
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.chat.id == OWNER_ID:
        await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=start_keyboard())

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def get_signal(message: types.Message):
    if message.chat.id != OWNER_ID:
        return
    await send_signal()

@dp.message_handler(lambda message: message.text == "🟢 Старт")
async def manual_start(message: types.Message):
    if message.chat.id == OWNER_ID:
        await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=start_keyboard())

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def handle_track(callback_query: CallbackQuery):
    coin_id = callback_query.data.split("track:")[1]
    tracker.track_coin(coin_id)
    await callback_query.answer(f"🟢 Отслеживание {coin_id} запущено")

@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    tracker.stop_all()
    await message.answer("⛔️ Все отслеживания остановлены.")

# === Клавиатура ===
def start_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Старт", callback_data="start"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="signal"),
    )
    keyboard.add(
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_all")
    )
    return keyboard

# === Старт ===
async def on_startup(_):
    logging.info("⏳ До следующего сигнала: 1167.0 минут")
    scheduler.start()
    tracker.run()

if __name__ == "__main__":
    keep_alive()
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
