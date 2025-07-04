import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio

from config import BOT_TOKEN, USER_ID
from signal_generator import generate_signal
from coin_tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot, USER_ID)

# Панель управления
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("🟢 Старт"),
    KeyboardButton("🚀 Получить ещё сигнал")
)
keyboard.add(
    KeyboardButton("🛑 Остановить все отслеживания")
)

# Обработка команды /start и кнопки Старт
@dp.message_handler(lambda message: message.text == "🟢 Старт")
async def start_handler(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    await message.answer("✅ Бот запущен. Жди сигнал каждый день в 08:00 по МСК.", reply_markup=keyboard)

# Обработка кнопки "Получить ещё сигнал"
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def handle_signal_request(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    result = generate_signal()
    if not result:
        await message.answer("⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    signal_text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"🔹 Символ: `{result['symbol']}`\n"
        f"📈 Текущая цена: *{result['price']} USDT*\n"
        f"🎯 Цель (+5%): *{result['target']}*\n"
        f"🛡️ Стоп-лосс: *{result['stop']}*\n"
        f"📊 Изменение за 24ч: *{result['change_24h']}%*\n"
        f"📈 RSI: *{result['rsi']}*\n"
        f"📉 MA7: *{result['ma7']}*, MA20: *{result['ma20']}*\n"
        f"🧠 Оценка: *{result['score']}*, Вероятность роста: *{result['probability']}%*"
    )

    inline_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{result['symbol']}:{result['price']}")
    )

    await message.answer(signal_text, reply_markup=inline_kb)

# Кнопка "Остановить все отслеживания"
@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    if message.from_user.id != USER_ID:
        return
    await tracker.stop_all_tracking()
    await message.answer("🔕 Все отслеживания остановлены.")

# Обработка inline кнопки "Следить за монетой"
@dp.callback_query_handler(lambda call: call.data.startswith("track:"))
async def handle_track_callback(call: types.CallbackQuery):
    if call.from_user.id != USER_ID:
        return
    _, symbol, price = call.data.split(":")
    await tracker.track_coin(symbol, float(price))
    await call.answer(f"🟡 Начато отслеживание {symbol} от {price} USDT", show_alert=True)

# Плановая ежедневная отправка сигнала
async def send_daily_signal():
    result = generate_signal()
    if result:
        signal_text = (
            f"💡 *Сигнал на рост: {result['name']}*\n\n"
            f"🔹 Символ: `{result['symbol']}`\n"
            f"📈 Текущая цена: *{result['price']} USDT*\n"
            f"🎯 Цель (+5%): *{result['target']}*\n"
            f"🛡️ Стоп-лосс: *{result['stop']}*\n"
            f"📊 Изменение за 24ч: *{result['change_24h']}%*\n"
            f"📈 RSI: *{result['rsi']}*\n"
            f"📉 MA7: *{result['ma7']}*, MA20: *{result['ma20']}*\n"
            f"🧠 Оценка: *{result['score']}*, Вероятность роста: *{result['probability']}%*"
        )

        inline_kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{result['symbol']}:{result['price']}")
        )

        await bot.send_message(USER_ID, signal_text, reply_markup=inline_kb)
    else:
        await bot.send_message(USER_ID, "⚠️ Сегодня подходящих монет нет. Завтра — новый день, новые возможности.")

# Планировщик запуска сигнала каждый день в 08:00 МСК
async def on_startup(dp):
    scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0, timezone="Europe/Moscow")
    scheduler.start()
    minutes_until_next_signal = (datetime.combine(datetime.now(), datetime.min.time()) + timedelta(days=1, hours=8) - datetime.now()).seconds // 60
    logger.info(f"⏳ До следующего сигнала: {minutes_until_next_signal} минут")
    print("✅ Бот готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
