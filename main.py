import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN, OWNER_ID
from analysis import get_top_3_cryptos
from tracking import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
coin_tracker = CoinTracker(bot)

# Клавиатура главного меню
main_keyboard = InlineKeyboardMarkup(row_width=2)
main_keyboard.add(
    InlineKeyboardButton("\U0001F7E2 Старт", callback_data="start"),
    InlineKeyboardButton("\U0001F680 Получить ещё сигнал", callback_data="more_signal"),
)
main_keyboard.add(
    InlineKeyboardButton("\U0001F6D1 Остановить все отслеживания", callback_data="stop_tracking")
)


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан\!\n\nБот готов к работе\.",
        reply_markup=main_keyboard
    )


@dp.callback_query_handler(lambda c: c.data == "start")
async def process_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "\U0001F4AC Я готов работать\!", reply_markup=main_keyboard)


@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    signal = await get_top_3_cryptos(1)
    if not signal:
        await bot.send_message(callback_query.from_user.id, "\u26A0\ufe0f Нет подходящих монет сейчас\.")
        return

    signal = signal[0]
    symbol = signal.get("symbol", "-")
    price = signal.get("price", 0)
    target = signal.get("target_price", 0)
    stop_loss = signal.get("stop_loss", 0)
    probability = signal.get("probability", 0)

    text = (
        f"\U0001F4C8 *Сигнал по монете:* {symbol}\n\n"
        f"\U0001F539 *Текущая цена:* ${price}\n"
        f"🎯 *Цель \(+5%\):* ${target}\n"
        f"🛑 *Стоп\-лосс \(\-3%\):* ${stop_loss}\n"
        f"📊 *Вероятность роста:* {probability}%"
    )

    signal_keyboard = InlineKeyboardMarkup(row_width=2)
    signal_keyboard.add(
        InlineKeyboardButton("Следить за монетой", callback_data=f"track_{symbol}"),
        InlineKeyboardButton("Получить ещё сигнал", callback_data="more_signal"),
        InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")
    )

    await bot.send_message(callback_query.from_user.id, text, reply_markup=signal_keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_")[1]
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"⏱ Запускаю отслеживание {symbol}\.")
    coin_tracker.add_tracking(callback_query.from_user.id, symbol)


@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    coin_tracker.remove_all_tracking(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "⛔️ Все отслеживания остановлены\.")


# Планировщик сигналов
async def daily_signal():
    signal = await get_top_3_cryptos(1)
    if not signal:
        return

    signal = signal[0]
    symbol = signal.get("symbol", "-")
    price = signal.get("price", 0)
    target = signal.get("target_price", 0)
    stop_loss = signal.get("stop_loss", 0)
    probability = signal.get("probability", 0)

    text = (
        f"\U0001F4C8 *Сигнал по монете:* {symbol}\n\n"
        f"\U0001F539 *Текущая цена:* ${price}\n"
        f"🎯 *Цель \(+5%\):* ${target}\n"
        f"🛑 *Стоп\-лосс \(\-3%\):* ${stop_loss}\n"
        f"📊 *Вероятность роста:* {probability}%"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Следить за монетой", callback_data=f"track_{symbol}")
    )
    await bot.send_message(OWNER_ID, text, reply_markup=keyboard)


scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
scheduler.add_job(coin_tracker.run, "interval", minutes=10)
scheduler.start()

logger.info("\u2705 Бот готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
