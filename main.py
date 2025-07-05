import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN, TELEGRAM_ID
from analysis import get_top_signals
from tracking import CoinTracker
from crypto_list import crypto_list

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

top_signals_cache = []
signal_index = 0
coin_tracker = CoinTracker(bot=bot)

start_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Получить ещё сигнал", callback_data="more_signal"),
    InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")
)


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан\\!\n\nБот готов к работе.",
        reply_markup=start_keyboard,
        parse_mode="MarkdownV2"
    )


@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def more_signal(callback_query: types.CallbackQuery):
    global signal_index, top_signals_cache

    if not top_signals_cache:
        top_signals_cache = await get_top_signals()
        signal_index = 0

    if not top_signals_cache:
        await callback_query.message.answer("⚠️ Не удалось получить сигналы. Попробуйте позже.")
        return

    if signal_index >= len(top_signals_cache):
        signal_index = 0

    signal = top_signals_cache[signal_index]
    signal_index += 1

    symbol = signal.get("symbol", "—")
    current_price = signal.get("price", 0)
    entry_price = round(current_price, 4)
    target_price = round(entry_price * 1.05, 4)
    stop_loss = round(entry_price * 0.97, 4)
    probability = signal.get("probability", 0)

    text = (
        f"📈 Сигнал по монете: *{symbol}*\n\n"
        f"🔹 Текущая цена: `${entry_price}`\n"
        f"🎯 Цель (+5%): `${target_price}`\n"
        f"🛑 Стоп-лосс (−3%): `${stop_loss}`\n"
        f"📊 Вероятность роста: *{probability}%*\n"
    )

    track_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Следить за монетой", callback_data=f"track_{symbol.lower()}"),
        InlineKeyboardButton("Получить ещё сигнал", callback_data="more_signal"),
        InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")
    )

    await callback_query.message.answer(text, reply_markup=track_keyboard, parse_mode="Markdown")


@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    coin_id = callback_query.data.split("track_")[1]
    await coin_tracker.add_coin(coin_id)
    await callback_query.message.answer(f"🟡 Монета *{coin_id.upper()}* добавлена в отслеживание.", parse_mode="Markdown")


@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await coin_tracker.stop_all()
    await callback_query.message.answer("🔕 Все отслеживания остановлены.")


async def daily_signal():
    top_signals = await get_top_signals()
    if top_signals:
        signal = top_signals[0]
        symbol = signal.get("symbol", "—")
        current_price = signal.get("price", 0)
        entry_price = round(current_price, 4)
        target_price = round(entry_price * 1.05, 4)
        stop_loss = round(entry_price * 0.97, 4)
        probability = signal.get("probability", 0)

        text = (
            f"📈 Утренний сигнал по монете: *{symbol}*\n\n"
            f"🔹 Текущая цена: `${entry_price}`\n"
            f"🎯 Цель (+5%): `${target_price}`\n"
            f"🛑 Стоп-лосс (−3%): `${stop_loss}`\n"
            f"📊 Вероятность роста: *{probability}%*"
        )

        track_keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Следить за монетой", callback_data=f"track_{symbol.lower()}")
        )

        await bot.send_message(chat_id=TELEGRAM_ID, text=text, reply_markup=track_keyboard, parse_mode="Markdown")


async def on_startup(_):
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(coin_tracker.run, "interval", minutes=10)
    scheduler.start()
    logger.info("✅ Бот готов к работе.")


if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
