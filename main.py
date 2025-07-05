import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

from analysis import analyze_all_coins, get_current_price
from tracking import CoinTracker
from crypto_list import crypto_list

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
OWNER_ID = 347552741

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot)

signal_cache = {
    "last_signals": [],
    "index": 0
}


def get_signal_message(signal):
    return (
        f"*Монета:* `{signal['coin_id']}`\n"
        f"*Вход:* ${signal['start_price']}\n"
        f"*Цель +5\\%:* ${round(signal['start_price'] * 1.05, 4)}\n"
        f"*Стоп\\-лосс \\-3\\%:* ${round(signal['start_price'] * 0.97, 4)}\n"
        f"*Вероятность роста:* *{signal['probability']}%*\n"
        f"_Изменение за 24ч: {signal['change_pct']}%_"
    )


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Получить ещё сигнал", callback_data="more_signal"),
        InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")
    )
    await message.answer("Добро пожаловать в новую жизнь, Корбан\\!\n\nБот готов к работе\\.", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'more_signal')
async def more_signal(callback_query: types.CallbackQuery):
    await callback_query.answer()
    if not signal_cache["last_signals"]:
        signals = analyze_all_coins(crypto_list)
        strong_signals = [s for s in signals if s["probability"] >= 65 and s["change_pct"] > -3]
        strong_signals.sort(key=lambda x: x["probability"], reverse=True)
        signal_cache["last_signals"] = strong_signals[:3]
        signal_cache["index"] = 0

    if signal_cache["last_signals"]:
        index = signal_cache["index"] % len(signal_cache["last_signals"])
        signal = signal_cache["last_signals"][index]
        signal_cache["index"] += 1

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['coin_id']}")
        )

        await bot.send_message(callback_query.from_user.id, get_signal_message(signal), reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, "Нет подходящих сигналов на данный момент.")


@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    await callback_query.answer()
    coin_id = callback_query.data.split("_", 1)[1]
    price = get_current_price(coin_id)
    if price:
        tracker.track_coin(callback_query.from_user.id, coin_id, price)
        await bot.send_message(callback_query.from_user.id, f"🔍 Начато отслеживание `{coin_id}` от ${price}")
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить цену монеты.")


@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await callback_query.answer()
    tracker.stop_all_tracking(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "⛔ Все отслеживания остановлены.")


async def daily_signal():
    signals = analyze_all_coins(crypto_list)
    strong_signals = [s for s in signals if s["probability"] >= 65 and s["change_pct"] > -3]
    strong_signals.sort(key=lambda x: x["probability"], reverse=True)
    if strong_signals:
        signal = strong_signals[0]
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['coin_id']}")
        )
        await bot.send_message(OWNER_ID, get_signal_message(signal), reply_markup=keyboard)
    else:
        await bot.send_message(OWNER_ID, "Нет сильных монет для сигнала сегодня.")


if __name__ == '__main__':
    scheduler.add_job(daily_signal, 'cron', hour=8, minute=0)
    scheduler.add_job(tracker.run, 'interval', minutes=10)
    scheduler.start()
    logger.info("✅ Бот готов к работе.")
    executor.start_polling(dp)
