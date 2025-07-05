# main.py — стабильный + логирование обработки сигнала

import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

@dp.message_handler(lambda message: message.text == "\U0001F4CA Получить ещё сигнал")
async def get_signal(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    logging.info("⚡ Обработка сигнала запущена")

    top_cryptos = get_top_3_cryptos()
    logging.info(f"🔍 top_cryptos: {top_cryptos}")

    if not top_cryptos:
        await message.answer("❌ Не удалось получить сигналы. Попробуй позже.")
        return

    for crypto in top_cryptos:
        signal = {
            "symbol": crypto["symbol"],
            "price": crypto["price"],
            "probability": crypto["probability"],
        }
        entry = signal["price"]
        target = entry * 1.05
        stop_loss = entry * 0.97

        msg = (
            f"\U0001F4C8 *Сигнал по монете:* {signal.get('symbol', '-')}\n"
            f"\U0001F3AF *Вероятность роста:* {signal.get('probability', 0)}%\n"
            f"\U0001F4B0 *Цена входа:* {entry:.4f} USD\n"
            f"\U0001F3AF *Цель:* {target:.4f} USD (+5%)\n"
            f"\U0001F6E1 *Стоп-лосс:* {stop_loss:.4f} USD (-3%)"
        )
        await message.answer(msg)

        # Запускаем отслеживание
        coin_data = {"symbol": crypto["symbol"], "id": crypto["symbol"].lower()}
        tracker = CoinTracker(bot, coin_data, entry)
        tracking_manager.add_tracker(tracker)

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
