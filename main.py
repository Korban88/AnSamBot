import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_list import crypto_list
from analysis import get_top_signals
from tracking import CoinTracker
import asyncio
import os
import re

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
OWNER_ID = 347552741

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Хранилище для состояния топ-3
top_signals_cache = []
current_signal_index = 0

# Экземпляр трекера
tracker = CoinTracker(bot, OWNER_ID)

# Экранируем символы для MarkdownV2
def escape_markdown(text):
    escape_chars = r"_\*\[\]\(\)~`>#+\-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\\\1", text)

def get_signal_message(signal):
    name = escape_markdown(signal['name'])
    price = signal['price']
    target = signal['target_price']
    stop = signal['stop_loss']
    prob = signal['probability']
    reason = escape_markdown(signal['reason'])

    return (
        f"*Сигнал на рост:* `{name}`\n"
        f"Текущая цена: *{price}*\n"
        f"Цель: *{target}*  (+5\%)\n"
        f"Стоп\-лосс: *{stop}*\n"
        f"Вероятность роста: *{prob}\%*\n"
        f"Причина: {reason}"
    )

def get_signal_keyboard(coin_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔍 Следить за монетой", callback_data=f"track:{coin_name}")]
    ])

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("\U0001F680 Получить ещё сигнал")
    keyboard.add("🛑 Остановить все отслеживания")
    await message.answer("Добро пожаловать в новую жизнь, Корбан!\n\nБот готов к работе.", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "🛑 Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    await tracker.stop_all_tracking()
    await message.answer("Все отслеживания остановлены.")

@dp.message_handler(lambda m: m.text == "🚀 Получить ещё сигнал")
async def more_signal(message: types.Message):
    global current_signal_index
    global top_signals_cache

    if not top_signals_cache:
        top_signals_cache = await get_top_signals(crypto_list)
        current_signal_index = 0

    if not top_signals_cache:
        await message.answer("Нет подходящих монет сейчас. Попробуй позже.")
        return

    if current_signal_index >= len(top_signals_cache):
        current_signal_index = 0

    signal = top_signals_cache[current_signal_index]
    current_signal_index += 1

    await bot.send_message(
        message.chat.id,
        get_signal_message(signal),
        reply_markup=get_signal_keyboard(signal['name'])
    )

@dp.callback_query_handler(lambda c: c.data.startswith('track:'))
async def track_coin(callback_query: types.CallbackQuery):
    coin = callback_query.data.split(':')[1]
    await tracker.track_coin(coin)
    await bot.answer_callback_query(callback_query.id, text=f"Отслеживаю {coin} на +3.5\% и +5\%")

async def daily_signal():
    top = await get_top_signals(crypto_list)
    if top:
        signal = top[0]
        await bot.send_message(
            OWNER_ID,
            get_signal_message(signal),
            reply_markup=get_signal_keyboard(signal['name'])
        )

# Планировщик ежедневного сигнала и отслеживания
scheduler.add_job(daily_signal, 'cron', hour=8, minute=0)
scheduler.add_job(tracker.run, 'interval', minutes=10)
scheduler.start()

if __name__ == '__main__':
    logger.info("\u2705 Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
