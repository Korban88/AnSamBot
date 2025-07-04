import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio

from config import BOT_TOKEN, USER_ID
from signal_generator import generate_signal
from tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

tracker = CoinTracker(bot, USER_ID)

main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("🔵 Старт", "🚀 Получить ещё сигнал")
main_keyboard.add("🔴 Остановить все отслеживания")

def get_watch_button(symbol):
    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton("👁 Следить за монетой", callback_data=f"watch_{symbol}"))
    return inline_kb

@dp.message_handler(commands=['start'])
@dp.message_handler(lambda message: message.text == "🔵 Старт")
async def start_handler(message: types.Message):
    await message.answer(
        "Бот активирован. Ждите сигналы каждый день в 8:00 МСК.",
        reply_markup=main_keyboard
    )

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def manual_signal_handler(message: types.Message):
    result = await generate_signal()
    if result:
        text = (
            f"💡 *Сигнал на рост: {result['name']}*
\n"
            f"🔹 Текущая цена: {result['current_price']:.4f} USDT\n"
            f"🌟 Цель: +5% → {result['target_price']:.4f} USDT\n"
            f"⛔️ Стоп-лосс: {result['stop_loss_price']:.4f} USDT\n"
            f"📊 Вероятность роста: *{result['probability']}%*\n"
            f"📈 RSI: {result['rsi']}, MA: {result['ma']}, 24h: {result['change_24h']}%\n"
        )
        await message.answer(text, reply_markup=get_watch_button(result['symbol']))
    else:
        await message.answer("⚠️ Нет подходящих монет для сигнала.")

@dp.message_handler(lambda message: message.text == "🔴 Остановить все отслеживания")
async def stop_all_handler(message: types.Message):
    tracker.stop_all()
    await message.answer("⛔️ Все отслеживания остановлены.")

@dp.callback_query_handler(lambda c: c.data.startswith("watch_"))
async def watch_handler(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_", 1)[1]
    tracker.track_coin(symbol)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"🔔 Теперь слежу за монетой {symbol}. Уведомлю при +3.5% или +5%.")

async def send_daily_signal():
    result = await generate_signal()
    if result:
        text = (
            f"💡 *Сигнал на рост: {result['name']}*
\n"
            f"🔹 Текущая цена: {result['current_price']:.4f} USDT\n"
            f"🌟 Цель: +5% → {result['target_price']:.4f} USDT\n"
            f"⛔️ Стоп-лосс: {result['stop_loss_price']:.4f} USDT\n"
            f"📊 Вероятность роста: *{result['probability']}%*\n"
            f"📈 RSI: {result['rsi']}, MA: {result['ma']}, 24h: {result['change_24h']}%\n"
        )
        await bot.send_message(USER_ID, text, reply_markup=get_watch_button(result['symbol']))
    else:
        await bot.send_message(USER_ID, "⚠️ Нет подходящих монет для сигнала.")

async def on_startup(_):
    scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0)
    scheduler.start()
    logger.info("⏳ До следующего сигнала: 1167.0 минут")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
