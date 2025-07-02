import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from crypto_utils import get_top_ton_wallet_coins
from tracking import start_tracking, stop_all_trackings

# === Настройки ===
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
ADMIN_ID = 347552741

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

# === Клавиатура ===
kb = InlineKeyboardMarkup(row_width=1)
kb.add(
    InlineKeyboardButton(text="Получить сигнал", callback_data="get_signal"),
    InlineKeyboardButton(text="Следить за монетой", callback_data="track_coin"),
    InlineKeyboardButton(text="Остановить все отслеживания", callback_data="stop_tracking")
)

# === Команда /start ===
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать! Бот активирован. Ждите сигналы каждый день в 8:00 МСК.",
        reply_markup=kb
    )

# === Callback обработчики ===
@dp.callback_query_handler(lambda c: c.data == "get_signal")
async def handle_get_signal(callback_query: types.CallbackQuery):
    await callback_query.answer()
    coin = get_top_ton_wallet_coins()
    if coin:
        price = coin['price']
        target_price = round(price * 1.05, 4)
        stop_loss_price = round(price * 0.965, 4)

        text = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10 + 10}%\n"
            f"🎯 Цель: {target_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_loss_price} $ (-3.5%)"
        )
        await bot.send_message(callback_query.from_user.id, text)
    else:
        await bot.send_message(callback_query.from_user.id, "Монеты не найдены.")

@dp.callback_query_handler(lambda c: c.data == "track_coin")
async def handle_track_coin(callback_query: types.CallbackQuery):
    await callback_query.answer()
    coin = get_top_ton_wallet_coins()
    if coin:
        await start_tracking(bot, callback_query.from_user.id, coin['id'], coin['price'])
        await bot.send_message(callback_query.from_user.id, f"🛰 Монета {coin['id']} отслеживается. Уведомим при росте +3.5% или по итогам 12ч.")
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось запустить отслеживание: монета не найдена.")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def handle_stop_tracking(callback_query: types.CallbackQuery):
    await callback_query.answer()
    stop_all_trackings(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "❌ Все отслеживания остановлены.")

# === Рассылка сигнала в 8:00 ===
async def scheduled_signal():
    coin = get_top_ton_wallet_coins()
    if coin:
        price = coin['price']
        target_price = round(price * 1.05, 4)
        stop_loss_price = round(price * 0.965, 4)

        text = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10 + 10}%\n"
            f"🎯 Цель: {target_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_loss_price} $ (-3.5%)"
        )
        await bot.send_message(ADMIN_ID, text)

# === Планировщик и запуск ===
scheduler.add_job(scheduled_signal, "cron", hour=8, minute=0)
async def on_startup(dp):
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
