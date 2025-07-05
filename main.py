import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TELEGRAM_TOKEN, TELEGRAM_ID
from analysis import get_top_signals
from tracking import CoinTracker
from crypto_list import crypto_list
from crypto_utils import get_current_price

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot)

top_signals_cache = []
signal_index = 0

# Инлайн-кнопки
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Старт", callback_data="start"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
    )
    keyboard.add(
        InlineKeyboardButton("🔴 Остановить все отслеживания", callback_data="stop_tracking")
    )
    return keyboard

# Приветственное сообщение
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = get_main_keyboard()
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан!\n\nБот готов к работе.",
        reply_markup=keyboard
    )

# Обработка кнопки Старт
@dp.callback_query_handler(lambda c: c.data == "start")
async def process_start(callback_query: types.CallbackQuery):
    await callback_query.answer("Бот уже активен.")

# Получить ещё сигнал
@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    global top_signals_cache, signal_index

    if not top_signals_cache:
        top_signals_cache = await get_top_signals()
        signal_index = 0

    if signal_index >= len(top_signals_cache):
        await bot.send_message(callback_query.from_user.id, "Новых сигналов пока нет.")
        return

    signal = top_signals_cache[signal_index]
    signal_index += 1

    message = (
        f"📈 Сигнал по монете: *{signal['symbol']}*\n\n"
        f"Вероятность роста: *{signal['probability']}%*\n"
        f"Цена входа: *{signal['entry_price']} USDT*\n"
        f"Цель +5%: *{signal['target_price']} USDT*\n"
        f"Стоп-лосс: *{signal['stop_loss']} USDT*"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")
    )

    await bot.send_message(callback_query.from_user.id, message, parse_mode="Markdown", reply_markup=keyboard)

# Кнопка "Следить за монетой"
@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_", 1)[1]
    await tracker.add_tracking(callback_query.from_user.id, symbol)
    await callback_query.answer(f"Начинаю отслеживание {symbol}.")

# Остановка отслеживаний
@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await tracker.stop_all_tracking(callback_query.from_user.id)
    await callback_query.answer("Все отслеживания остановлены.")

# Автосигнал каждое утро
async def daily_signal():
    top_signals = await get_top_signals()
    if not top_signals:
        return

    signal = top_signals[0]
    message = (
        f"📈 Утренний сигнал по монете: *{signal['symbol']}*\n\n"
        f"Вероятность роста: *{signal['probability']}%*\n"
        f"Цена входа: *{signal['entry_price']} USDT*\n"
        f"Цель +5%: *{signal['target_price']} USDT*\n"
        f"Стоп-лосс: *{signal['stop_loss']} USDT*"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")
    )

    await bot.send_message(TELEGRAM_ID, message, parse_mode="Markdown", reply_markup=keyboard)

if __name__ == "__main__":
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(tracker.run, "interval", minutes=10)
    scheduler.start()
    logger.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
