import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import CantParseEntities
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

from config import TELEGRAM_TOKEN, OWNER_ID
from analysis import get_top_cryptos
from tracking import CoinTrackingManager
from crypto_utils import get_current_price

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

coin_tracking_manager = CoinTrackingManager()
top_coins_cache = []
last_signal_index = 0


@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔️ У вас нет доступа к этому боту.")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Получить сигнал", callback_data="get_signal"),
        InlineKeyboardButton("⛔️ Остановить все отслеживания", callback_data="stop_tracking")
    )

    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан\!\n\n*AnSam Bot* готов дать тебе прибыльные сигналы\. Выбери действие:",
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data == "get_signal")
async def get_signal(callback_query: types.CallbackQuery):
    global last_signal_index, top_coins_cache

    await bot.answer_callback_query(callback_query.id)

    if not top_coins_cache:
        top_coins_cache = get_top_cryptos()
        last_signal_index = 0

    if last_signal_index >= len(top_coins_cache):
        await bot.send_message(callback_query.from_user.id, "✅ Сигналы на сегодня закончились.")
        return

    signal = top_coins_cache[last_signal_index]
    last_signal_index += 1

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['id']}")
    )

    try:
        await bot.send_message(
            callback_query.from_user.id,
            f"📈 *Сигнал по монете:* {signal.get('symbol', '-')}\n"
            f"🎯 Цель: +5\\%\n"
            f"📊 Цена входа: ${signal.get('entry_price', '-')}\n"
            f"📉 Стоп\\-лосс: ${signal.get('stop_loss', '-')}\n"
            f"📈 Вероятность роста: *{signal.get('growth_probability', '-')}\\%*\n",
            reply_markup=keyboard
        )
    except CantParseEntities as e:
        logger.error(f"Ошибка форматирования Markdown: {e}")
        await bot.send_message(callback_query.from_user.id, "⚠️ Ошибка отображения сигнала.")


@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_coin(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    coin_id = callback_query.data.split("_", 1)[1]
    coin = next((c for c in top_coins_cache if c["id"] == coin_id), None)

    if not coin:
        await bot.send_message(callback_query.from_user.id, "⚠️ Монета не найдена.")
        return

    current_price = get_current_price(coin["id"])
    if current_price is None:
        await bot.send_message(callback_query.from_user.id, "⚠️ Не удалось получить цену монеты.")
        return

    from tracking import CoinTracker
    tracker = CoinTracker(bot, coin, current_price)
    coin_tracking_manager.add_tracker(tracker)

    await bot.send_message(callback_query.from_user.id, f"👁 Начато отслеживание монеты {coin['symbol'].upper()}.")


@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_all_tracking(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    coin_tracking_manager.stop_all()
    await bot.send_message(callback_query.from_user.id, "⛔️ Все отслеживания остановлены.")


async def daily_signal():
    global top_coins_cache, last_signal_index
    top_coins_cache = get_top_cryptos()
    last_signal_index = 0

    if not top_coins_cache:
        logger.warning("Нет доступных сигналов.")
        return

    signal = top_coins_cache[0]
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['id']}")
    )

    try:
        await bot.send_message(
            OWNER_ID,
            f"📈 *Утренний сигнал: {signal['symbol'].upper()}*\n"
            f"🎯 Цель: +5\\%\n"
            f"📊 Цена входа: ${signal['entry_price']}\n"
            f"📉 Стоп\\-лосс: ${signal['stop_loss']}\n"
            f"📈 Вероятность роста: *{signal['growth_probability']}\\%*",
            reply_markup=keyboard
        )
    except CantParseEntities as e:
        logger.error(f"Ошибка форматирования Markdown: {e}")
        await bot.send_message(OWNER_ID, "⚠️ Ошибка отображения утреннего сигнала.")


scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
scheduler.start()

if __name__ == "__main__":
    logger.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
