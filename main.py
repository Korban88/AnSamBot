import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TELEGRAM_TOKEN, TELEGRAM_ID
from analysis import get_top_signals
from tracking import CoinTracker

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
tracker = CoinTracker(bot)
top_signals_cache = []
top_index = 0

def get_signal_message(signal: dict) -> str:
    return (
        f"Монета: *{signal['coin'].upper()}*\n"
        f"Цена входа: `{signal['entry_price']}`\n"
        f"Цель +5%: `{signal['target_price']}`\n"
        f"Стоп-лосс: `{signal['stop_loss']}`\n"
        f"Вероятность роста: *{signal['probability']}%*"
    )

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Получить ещё сигнал", callback_data="more"))
    keyboard.add(InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking"))
    await message.answer("Добро пожаловать в новую жизнь, Корбан!\n\nБот готов к работе.", reply_markup=keyboard, parse_mode="MarkdownV2")

@dp.callback_query_handler(lambda c: c.data == "more")
async def more_signal(callback_query: types.CallbackQuery):
    global top_signals_cache, top_index

    if not top_signals_cache:
        top_signals_cache = await get_top_signals()
        top_index = 0

    if top_index >= len(top_signals_cache):
        await bot.send_message(callback_query.from_user.id, "Новых сигналов пока нет.")
        return

    signal = top_signals_cache[top_index]
    top_index += 1

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['coin']}"))
    await bot.send_message(callback_query.from_user.id, get_signal_message(signal), reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    coin = callback_query.data.split("_", 1)[1]
    price = await get_current_price(coin)

    if not price:
        await bot.send_message(callback_query.from_user.id, f"Не удалось получить цену для {coin}.")
        return

    tracker.track_coin(coin, price)
    await bot.send_message(callback_query.from_user.id, f"Запущено отслеживание монеты {coin.upper()} по цене {price}")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    tracker.tracked.clear()
    await bot.send_message(callback_query.from_user.id, "Все отслеживания остановлены.")

async def daily_signal():
    top_signals = await get_top_signals()
    if top_signals:
        signal = top_signals[0]
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['coin']}"))
        await bot.send_message(TELEGRAM_ID, get_signal_message(signal), reply_markup=keyboard, parse_mode="Markdown")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(tracker.run, "interval", minutes=10)
    scheduler.start()
    logging.info("✅ Бот готов к работе.")
    from crypto_utils import get_current_price
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
