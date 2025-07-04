import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

from config import BOT_TOKEN, USER_ID
from signal_generator import generate_signal
from coin_tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot)

# Кнопки
keyboard = InlineKeyboardMarkup(row_width=2)
keyboard.add(
    InlineKeyboardButton("🟢 Старт", callback_data="start"),
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="get_signal"),
    InlineKeyboardButton("🔴 Остановить все отслеживания", callback_data="stop_all")
)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    logger.info("\U0001F7E2 Команда /start получена")
    await message.answer("\u2705 Бот запущен. Выбирай действие:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'start')
async def process_start(callback_query: types.CallbackQuery):
    logger.info("\u2705 Нажата кнопка Старт")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "\u2705 Бот готов. Жми \"\ud83d\ude80 Получить ещё сигнал\" или \"\ud83d\udd34 Остановить все отслеживания\".", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'get_signal')
async def process_get_signal(callback_query: types.CallbackQuery):
    logger.info("\u23F0 Получение сигнала...")
    await bot.answer_callback_query(callback_query.id)
    result = generate_signal()

    if not result:
        await bot.send_message(callback_query.from_user.id, "\u26A0\ufe0f Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    text = (
        f"\ud83d\udca1 *Сигнал на рост: {result['name']} ({result['symbol']})*

"
        f"Цена входа: *{result['entry']} $
"
        f"Цель: +5% → {result['target']} $
"
        f"Stop-loss: {result['stop']} $
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"Изменение за 24ч: {result['change_24h']:.2f}%
"
        f"RSI: {result['rsi']:.2f}
"
        f"MA(7): {result['ma7']:.4f}, MA(20): {result['ma20']:.4f}"
    )

    # Кнопка отслеживания монеты
    follow_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("\ud83d\udc41 Следить за монетой", callback_data=f"follow_{result['symbol']}")
    )

    await bot.send_message(callback_query.from_user.id, text, reply_markup=follow_keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('follow_'))
async def process_follow(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split('_', 1)[1]
    logger.info(f"\U0001F441 Запущено отслеживание монеты: {symbol}")
    await bot.answer_callback_query(callback_query.id)
    await tracker.track_coin(symbol, callback_query.from_user.id)

@dp.callback_query_handler(lambda c: c.data == 'stop_all')
async def process_stop(callback_query: types.CallbackQuery):
    logger.info("\u274C Остановка всех отслеживаний")
    await bot.answer_callback_query(callback_query.id)
    await tracker.stop_all(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "\u274c Все отслеживания остановлены.")

async def send_daily_signal():
    logger.info("\ud83d\udd52 Запуск ежедневного сигнала")
    result = generate_signal()
    if not result:
        await bot.send_message(USER_ID, "\u26A0\ufe0f Сегодня нет подходящих монет. Попробуем завтра.")
        return

    text = (
        f"\ud83d\udca1 *Сигнал на рост: {result['name']} ({result['symbol']})*

"
        f"Цена входа: *{result['entry']} $
"
        f"Цель: +5% → {result['target']} $
"
        f"Stop-loss: {result['stop']} $
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"Изменение за 24ч: {result['change_24h']:.2f}%
"
        f"RSI: {result['rsi']:.2f}
"
        f"MA(7): {result['ma7']:.4f}, MA(20): {result['ma20']:.4f}"
    )

    follow_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("\ud83d\udc41 Следить за монетой", callback_data=f"follow_{result['symbol']}")
    )

    await bot.send_message(USER_ID, text, reply_markup=follow_keyboard)

async def on_startup(dp):
    scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0)
    scheduler.start()
    logger.info("\u23f3 До следующего сигнала: 1167.0 минут")
    await asyncio.sleep(1)
    print("\u2705 Бот готов к работе.")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
