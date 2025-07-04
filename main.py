import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analysis import analyze_all_coins, get_current_price
from coin_tracker import CoinTracker
from config import BOT_TOKEN, USER_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
coin_tracker = CoinTracker(bot, USER_ID)
signal_index = {}

start_keyboard = InlineKeyboardMarkup(row_width=1)
start_keyboard.add(
    InlineKeyboardButton("🟢 Старт", callback_data="start"),
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
    InlineKeyboardButton("🔴 Остановить все отслеживания", callback_data="stop_tracking")
)

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    signal_index[message.chat.id] = 0
    await message.answer("✅ Я готов искать сигналы. Жми «Получить ещё сигнал».", reply_markup=start_keyboard)

@dp.callback_query_handler(lambda c: c.data == "start")
async def start_callback(callback_query: types.CallbackQuery):
    signal_index[callback_query.message.chat.id] = 0
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "✅ Бот запущен. Я готов искать сигналы по криптовалютам.", reply_markup=start_keyboard)

@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)

    signals = analyze_all_coins()
    if not signals:
        await bot.send_message(user_id, "⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    idx = signal_index.get(user_id, 0) % len(signals)
    signal = signals[idx]
    signal_index[user_id] = idx + 1

    symbol = signal["symbol"]
    entry = signal["current_price"]
    target = round(entry * 1.05, 6)
    stop_loss = round(entry * 0.97, 6)

    message = (
        f"📈 *Сигнал на рост монеты* `{symbol.upper()}`\n\n"
        f"*🎯 Цель:* +5% → `{target} $`\n"
        f"*💰 Цена входа:* `{entry} $`\n"
        f"*🛑 Стоп-лосс:* `{stop_loss} $`\n"
        f"*📊 Прогноз роста:* {signal['probability']}%\n"
        f"*📉 Изменение за 24ч:* {signal['change_percent']}%"
    )

    follow_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f"👁 Следить за монетой {symbol.upper()}", callback_data=f"follow_{symbol}")
    )

    await bot.send_message(user_id, message, reply_markup=follow_button)

@dp.callback_query_handler(lambda c: c.data.startswith("follow_"))
async def follow_coin(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_")[1]
    price = get_current_price(symbol)
    if price:
        coin_tracker.track_coin(symbol, price)
        await bot.send_message(callback_query.from_user.id, f"👁 Я начал следить за *{symbol.upper()}* по цене {price} $.")
    else:
        await bot.send_message(callback_query.from_user.id, f"⚠️ Не удалось получить цену для {symbol.upper()}.")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    coin_tracker.tracked_coins.clear()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "🛑 Все отслеживания остановлены.")

async def daily_signal():
    logging.info("⏰ Отправка утреннего сигнала")
    signals = analyze_all_coins()
    if not signals:
        await bot.send_message(USER_ID, "⚠️ Сегодня нет подходящих сигналов.")
        return

    signal = signals[0]
    symbol = signal["symbol"]
    entry = signal["current_price"]
    target = round(entry * 1.05, 6)
    stop_loss = round(entry * 0.97, 6)

    message = (
        f"🌅 *Утренний сигнал на {symbol.upper()}*\n\n"
        f"*🎯 Цель:* +5% → `{target} $`\n"
        f"*💰 Вход:* `{entry} $`\n"
        f"*🛑 Стоп:* `{stop_loss} $`\n"
        f"*📊 Прогноз:* {signal['probability']}%\n"
        f"*📉 За 24ч:* {signal['change_percent']}%"
    )

    follow_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f"👁 Следить за монетой {symbol.upper()}", callback_data=f"follow_{symbol}")
    )

    await bot.send_message(USER_ID, message, reply_markup=follow_button)

if __name__ == "__main__":
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0, timezone="Europe/Moscow")
    scheduler.add_job(coin_tracker.run, "interval", minutes=10)
    scheduler.start()
    logging.info("✅ Бот готов к работе.")
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
