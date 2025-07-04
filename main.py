import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from tracker import CoinTracker
from signal_generator import generate_signal
from config import BOT_TOKEN, USER_ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Клавиатура (нижняя панель)
main_keyboard = InlineKeyboardMarkup(row_width=2)
main_keyboard.add(
    InlineKeyboardButton("🟢 Старт", callback_data="start"),
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="get_signal"),
    InlineKeyboardButton("🔴 Остановить все отслеживания", callback_data="stop_tracking")
)

# Объект трекера
tracker = CoinTracker(bot, USER_ID)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=main_keyboard)

@dp.callback_query_handler(lambda c: c.data == "start")
async def process_start(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "get_signal")
async def process_get_signal(callback_query: types.CallbackQuery):
    result = await generate_signal()
    if result is None:
        await callback_query.message.answer("⚠️ Нет подходящих монет для сигнала.")
        await callback_query.answer()
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*
"
        f"Цена входа: {result['entry_price']}
"
        f"Цель (5%): {result['target_price']}
"
        f"Стоп-лосс: {result['stop_loss']}
"
        f"Вероятность: {result['probability']}%
"
        f"Δ24ч: {result['change_24h']}% | RSI: {result['rsi']} | MA: {result['ma_trend']}"
    )

    follow_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{result['name']}:{result['entry_price']}")
    )
    await callback_query.message.answer(text, reply_markup=follow_button)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("track:"))
async def handle_track_coin(callback_query: types.CallbackQuery):
    parts = callback_query.data.split(":")
    if len(parts) != 3:
        await callback_query.answer("Ошибка отслеживания")
        return
    coin, entry = parts[1], float(parts[2])
    await tracker.track_coin(coin, entry)
    await callback_query.answer(f"Монета {coin} добавлена для отслеживания")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_all_tracking(callback_query: types.CallbackQuery):
    await tracker.stop_all_tracking()
    await callback_query.answer("Отслеживание монет остановлено")

async def send_daily_signal():
    result = await generate_signal()
    if result:
        text = (
            f"💡 *Сигнал на рост: {result['name']}*
"
            f"Цена входа: {result['entry_price']}
"
            f"Цель (5%): {result['target_price']}
"
            f"Стоп-лосс: {result['stop_loss']}
"
            f"Вероятность: {result['probability']}%
"
            f"Δ24ч: {result['change_24h']}% | RSI: {result['rsi']} | MA: {result['ma_trend']}"
        )
        follow_button = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{result['name']}:{result['entry_price']}")
        )
        await bot.send_message(USER_ID, text, reply_markup=follow_button)

# Планировщик запуска сигналов каждый день в 8:00 МСК
scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
scheduler.start()

if __name__ == "__main__":
    logging.info("⏳ До следующего сигнала: 1167.0 минут")
    executor.start_polling(dp, skip_updates=True)
