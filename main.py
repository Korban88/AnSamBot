import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from crypto_utils import get_top_ton_wallet_coins
from tracking import start_tracking, stop_all_trackings

# === Настройки ===
BOT_TOKEN = "ТОКЕН_СЮДА"
ADMIN_ID = 347552741

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
logging.basicConfig(level=logging.INFO)

# === Клавиатура меню ===
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    types.KeyboardButton("🟢 Старт"),
    types.KeyboardButton("🚀 Получить ещё сигнал"),
    types.KeyboardButton("👁 Следить за монетой"),
    types.KeyboardButton("🛑 Остановить все отслеживания")
)

# === /start ===
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать! Бот активирован. Ждите сигналы каждый день в 8:00 МСК.",
        reply_markup=main_menu
    )

# === Кнопка 'Старт' — повторяет /start ===
@dp.message_handler(lambda message: message.text == "🟢 Старт")
async def start_again(message: types.Message):
    await message.answer(
        "Бот активирован. Ждите сигналы каждый день в 8:00 МСК.",
        reply_markup=main_menu
    )

# === Кнопка 'Получить ещё сигнал' ===
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    try:
        coins = get_top_ton_wallet_coins(top_n=3)
        if not coins:
            await message.answer("Не удалось найти подходящие монеты.")
            return

        for coin in coins:
            price = coin['price']
            target_price = round(price * 1.05, 4)
            stop_loss_price = round(price * 0.965, 4)
            text = (
                f"💰 Сигнал:\n"
                f"Монета: {coin['id']}\n"
                f"Цена: {price} $\n"
                f"Рост за 24ч: {coin['change_24h']}%\n"
                f"Вероятность роста: {coin['probability']}%\n"
                f"🎯 Цель: {target_price} $ (+5%)\n"
                f"⛔️ Стоп-лосс: {stop_loss_price} $ (-3.5%)"
            )
            await message.answer(text)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при получении сигнала: {str(e)}")

# === Кнопка 'Следить за монетой' ===
@dp.message_handler(lambda message: message.text == "👁 Следить за монетой")
async def handle_track_coin(message: types.Message):
    coins = get_top_ton_wallet_coins(top_n=1)
    if coins:
        coin = coins[0]
        await start_tracking(bot, message.from_user.id, coin['id'], coin['price'])
        await message.answer(
            f"🛰 Монета {coin['id']} отслеживается. Уведомим при +3.5%, +5% или по итогам 12ч."
        )
    else:
        await message.answer("Не удалось запустить отслеживание: монета не найдена.")

# === Кнопка 'Остановить все отслеживания' ===
@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    stop_all_trackings(message.from_user.id)
    await message.answer("❌ Все отслеживания остановлены.")

# === Ежедневный сигнал в 8:00 ===
async def scheduled_signal():
    coins = get_top_ton_wallet_coins(top_n=1)
    if coins:
        coin = coins[0]
        price = coin['price']
        target_price = round(price * 1.05, 4)
        stop_loss_price = round(price * 0.965, 4)
        text = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['probability']}%\n"
            f"🎯 Цель: {target_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_loss_price} $ (-3.5%)"
        )
        await bot.send_message(ADMIN_ID, text)

# === Планировщик ===
scheduler.add_job(scheduled_signal, "cron", hour=8, minute=0)
async def on_startup(dp):
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
