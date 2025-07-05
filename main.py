import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analysis import get_top_signals
from tracking import CoinTracker
from config import TELEGRAM_TOKEN, TELEGRAM_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

coin_tracker = CoinTracker(bot=bot, user_id=TELEGRAM_ID)

top_signals_cache = []
current_signal_index = 0

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Старт", callback_data="start"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
    )
    keyboard.add(
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
    )
    return keyboard

def get_signal_message(signal: dict) -> str:
    return (
        f"<b>{signal['name']}</b>\n\n"
        f"📈 <b>Вероятность роста:</b> {signal['probability']}%\n"
        f"🎯 <b>Цель:</b> +5%\n"
        f"💰 <b>Цена входа:</b> {signal['entry_price']}\n"
        f"🛑 <b>Стоп-лосс:</b> {signal['stop_loss']}\n"
        f"📊 <b>Изменение за 24ч:</b> {signal['change_24h']}%\n"
        f"📉 <b>RSI:</b> {signal['rsi']}\n"
        f"🧠 <i>{signal['reason']}</i>"
    )

async def daily_signal():
    global top_signals_cache, current_signal_index
    logging.info("⏰ Генерация утреннего сигнала...")
    top_signals_cache = await get_top_signals()
    current_signal_index = 0

    if top_signals_cache:
        signal = top_signals_cache[current_signal_index]
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")
        )
        await bot.send_message(TELEGRAM_ID, get_signal_message(signal), reply_markup=keyboard, parse_mode="HTML")
        logging.info("✅ Сигнал отправлен.")
    else:
        await bot.send_message(TELEGRAM_ID, "⚠️ Сегодня нет подходящих монет.", parse_mode="HTML")
        logging.warning("❌ Сигналы не найдены.")

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = get_main_keyboard()
    await message.answer("Добро пожаловать в новую жизнь, Корбан!\n\nБот готов к работе.", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "start")
async def start_callback(callback_query: types.CallbackQuery):
    keyboard = get_main_keyboard()
    await bot.send_message(callback_query.from_user.id, "Добро пожаловать в новую жизнь, Корбан!\n\nБот готов к работе.", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    global current_signal_index, top_signals_cache
    if not top_signals_cache:
        top_signals_cache = await get_top_signals()
        current_signal_index = 0

    if current_signal_index >= len(top_signals_cache):
        await bot.send_message(callback_query.from_user.id, "⚠️ Больше сигналов на сегодня нет.", parse_mode="HTML")
        return

    signal = top_signals_cache[current_signal_index]
    current_signal_index += 1

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")
    )
    await bot.send_message(callback_query.from_user.id, get_signal_message(signal), reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_", 1)[1]
    await coin_tracker.add_coin(symbol)
    await bot.send_message(callback_query.from_user.id, f"👁 Монета <b>{symbol}</b> теперь под наблюдением. Уведомим при росте на +3.5% и +5%.", parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await coin_tracker.clear_tracking()
    await bot.send_message(callback_query.from_user.id, "🛑 Все отслеживания остановлены.", parse_mode="HTML")

if __name__ == "__main__":
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(coin_tracker.run, "interval", minutes=10)
    scheduler.start()
    logging.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
