import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import TELEGRAM_TOKEN, OWNER_ID
from analysis import get_top_3_cryptos
from tracking import CoinTracker, CoinTrackingManager

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Инициализация менеджера отслеживания
tracking_manager = CoinTrackingManager()

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["\U0001F4CA Получить ещё сигнал", "\U0001F6D1 Остановить все отслеживания"]
    keyboard.add(*buttons)

    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан!\n\n"
        "Бот готов присылать крипто-сигналы с высоким потенциалом роста.",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: message.text == "📊 Получить ещё сигнал")
async def get_signal(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    logging.info("⚡ Обработка сигнала запущена")

    try:
        top_cryptos = get_top_3_cryptos()
        if not top_cryptos:
            logging.warning("❌ Топ-3 монет не найден")
            await message.answer("❌ Не удалось получить сигналы. Попробуй позже.")
            return

        for crypto in top_cryptos:
            logging.info(f"🔹 Сигнал: {crypto['symbol']} — {crypto['probability']}% — {crypto['price']} USD")
            entry = crypto["price"]
            target = entry * 1.05
            stop_loss = entry * 0.97

            msg = (
                f"📈 *Сигнал по монете:* {crypto['symbol']}\n"
                f"🎯 *Вероятность роста:* {crypto['probability']}%\n"
                f"💰 *Цена входа:* {entry:.4f} USD\n"
                f"🎯 *Цель:* {target:.4f} USD (+5%)\n"
                f"🛡 *Стоп-лосс:* {stop_loss:.4f} USD (-3%)"
            )
            await message.answer(msg)

            # Кнопка "Следить за монетой"
            track_button = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{crypto['symbol'].lower()}|{entry}")
            )
            await message.answer(" ", reply_markup=track_button)

    except Exception as e:
        logging.error(f"❌ Ошибка в get_signal: {e}")
        await message.answer("⚠️ Ошибка при получении сигнала.")

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def process_track_callback(callback_query: CallbackQuery):
    try:
        data = callback_query.data.replace("track_", "").split("|")
        symbol = data[0]
        price = float(data[1])

        coin_data = {"symbol": symbol.upper(), "id": symbol.lower()}
        tracker = CoinTracker(bot, coin_data, price)
        tracking_manager.add_tracker(tracker)

        await callback_query.answer("Монета добавлена в отслеживание!", show_alert=True)
    except Exception as e:
        logging.error(f"❌ Ошибка в process_track_callback: {e}")
        await callback_query.answer("⚠️ Не удалось запустить отслеживание.", show_alert=True)

@dp.message_handler(lambda message: message.text == "\U0001F6D1 Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    tracking_manager.trackers.clear()
    await message.answer("\U0001F6D1 Все отслеживания остановлены.")

# Ежедневный сигнал
async def daily_signal():
    try:
        top_cryptos = get_top_3_cryptos()
        if not top_cryptos:
            return

        crypto = top_cryptos[0]
        entry = crypto["price"]
        target = entry * 1.05
        stop_loss = entry * 0.97

        msg = (
            f"\U0001F4C8 *Сигнал на сегодня:* {crypto['symbol']}\n"
            f"\U0001F3AF *Вероятность:* {crypto['probability']}%\n"
            f"\U0001F4B0 *Цена входа:* {entry:.4f} USD\n"
            f"\U0001F3AF *Цель:* {target:.4f} USD (+5%)\n"
            f"\U0001F6E1 *Стоп-лосс:* {stop_loss:.4f} USD"
        )
        await bot.send_message(OWNER_ID, msg)

        coin_data = {"symbol": crypto["symbol"], "id": crypto["symbol"].lower()}
        tracker = CoinTracker(bot, coin_data, entry)
        tracking_manager.add_tracker(tracker)

    except Exception as e:
        logging.error(f"Ошибка при отправке ежедневного сигнала: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
    scheduler.add_job(tracking_manager.run, "interval", minutes=10)
    scheduler.start()
    logging.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
