import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analysis import get_top_signals
from tracking import CoinTracker
from config import TELEGRAM_TOKEN, OWNER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Создаём экземпляр CoinTracker
coin_tracker = CoinTracker()

# Главное меню
main_keyboard = InlineKeyboardMarkup(row_width=2)
main_keyboard.add(
    InlineKeyboardButton("🟢 Старт", callback_data="start"),
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
)
main_keyboard.add(
    InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = main_keyboard
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан\!\n\nБот готов к работе\.",
        reply_markup=keyboard,
    )

@dp.callback_query_handler(lambda c: c.data == "start")
async def process_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Бот уже запущен и готов к работе.")

@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    signals = await get_top_signals()
    if not signals:
        await callback_query.message.answer("Нет подходящих сигналов сейчас.")
        return

    signal = signals[0]  # Первый из топа
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Следить за монетой", callback_data=f"track_{signal['id']}"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
    )

    text = (
        f"📈 *Сигнал по монете:* {signal.get('symbol', '-')}
"
        f"💎 Текущая цена: \${signal.get('price', 0)}
"
        f"🎯 Цель (+5%): \${signal.get('target_price', 0)}
"
        f"🛑 Стоп-лосс (−3%): \${signal.get('stop_loss', 0)}
"
        f"📊 Вероятность роста: *{signal.get('probability', 0)}%*"
    )
    await callback_query.message.answer(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    coin_id = callback_query.data.split("_")[1]
    await bot.answer_callback_query(callback_query.id)
    await coin_tracker.track_current(bot, coin_id, OWNER_ID)
    await callback_query.message.answer(f"Монета {coin_id} отслеживается. Уведомим при росте +3.5% или +5%.")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    coin_tracker.stop_all()
    await callback_query.message.answer("Все отслеживания остановлены.")

# Запускаем задачи
scheduler.add_job(coin_tracker.run, "interval", minutes=10)
scheduler.add_job(lambda: asyncio.create_task(daily_signal()), "cron", hour=8, minute=0)
scheduler.start()

async def daily_signal():
    signals = await get_top_signals()
    if not signals:
        return

    signal = signals[0]  # Топ-1 монета
    text = (
        f"📈 *Сигнал по монете:* {signal.get('symbol', '-')}
"
        f"💎 Текущая цена: \${signal.get('price', 0)}
"
        f"🎯 Цель (+5%): \${signal.get('target_price', 0)}
"
        f"🛑 Стоп-лосс (−3%): \${signal.get('stop_loss', 0)}
"
        f"📊 Вероятность роста: *{signal.get('probability', 0)}%*"
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Следить за монетой", callback_data=f"track_{signal['id']}"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
    )
    await bot.send_message(OWNER_ID, text, reply_markup=keyboard)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
