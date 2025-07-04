import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from signal_generator import generate_signal
from coin_tracker import CoinTracker
from config import BOT_TOKEN, USER_ID
import asyncio

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Трекер
tracker = CoinTracker(bot, USER_ID)

# Кеш топ-3
top3_cache = []
top3_index = 0


def format_signal(result):
    explanation = (
        f"*💡 Сигнал на рост: {result['name']} ({result['symbol']})*\n"
        f"Цена входа: *{result['entry']}*\n"
        f"🎯 Цель (+5%): *{result['target']}*\n"
        f"🛡️ Стоп-лосс (−3.5%): *{result['stop']}*\n\n"
        f"*📊 Метрики:*\n"
        f"— Изменение за 24ч: {result['change_24h']}%\n"
        f"— RSI: {result['rsi']}\n"
        f"— MA7: {result['ma7']}\n"
        f"— MA20: {result['ma20']}\n"
        f"— Оценка: {result['score']} / Вероятность роста: *{result['probability']}%*"
    )
    return explanation


def get_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Старт", callback_data="start"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="get_signal"),
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
    )
    return keyboard


def get_signal_keyboard(symbol):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{symbol}"))
    return keyboard


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("✅ Я готов искать сигналы. Жми «Получить ещё сигнал».", reply_markup=get_main_menu())


@dp.callback_query_handler(lambda c: c.data == "start")
async def start_callback(callback_query: types.CallbackQuery):
    await callback_query.answer("Ты нажал Старт")
    await callback_query.message.answer("✅ Бот запущен. Я готов искать сигналы по криптовалютам.")


@dp.callback_query_handler(lambda c: c.data == "get_signal")
async def signal_callback(callback_query: types.CallbackQuery):
    await callback_query.answer("Ты запросил сигнал")
    await send_signal(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_callback(callback_query: types.CallbackQuery):
    await callback_query.answer("Отслеживание остановлено")
    await tracker.clear()
    await callback_query.message.answer("🛑 Все отслеживания остановлены.")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def track_callback(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split(":")[1]
    await callback_query.answer("🔍 Монета добавлена в отслеживание")
    await tracker.add(symbol)


async def send_signal(message: types.Message):
    global top3_cache, top3_index

    if not top3_cache or top3_index >= len(top3_cache):
        top3_cache = generate_signal(return_top3=True)
        top3_index = 0

    if not top3_cache:
        await message.answer("⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    result = top3_cache[top3_index]
    top3_index += 1

    msg = format_signal(result)
    keyboard = get_signal_keyboard(result["symbol"])
    await message.answer(msg, reply_markup=keyboard)


async def send_daily_signal():
    logger.info("⏰ Генерация утреннего сигнала")
    result = generate_signal()
    if result:
        msg = format_signal(result)
        keyboard = get_signal_keyboard(result["symbol"])
        await bot.send_message(USER_ID, msg, reply_markup=keyboard)
    else:
        await bot.send_message(USER_ID, "⚠️ Пока нет монет с высоким потенциалом. Проверю позже.")


async def on_startup(dp):
    scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(tracker.run, "interval", minutes=10)
    scheduler.start()
    logger.info("✅ Бот готов к работе.")


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
