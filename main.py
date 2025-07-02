import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import get_top_ton_wallet_coins
from tracking import start_tracking
import asyncio

API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# --- Кнопки ---
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("👁 Следить за монетой"))

# --- Старт ---
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def manual_signal(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        price = coin['price']
        goal_price = round(price * 1.05, 4)
        stop_price = round(price * 0.965, 4)
        signal = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10 + 50}%\n"
            f"🎯 Цель: {goal_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_price} $ (-3.5%)"
        )
        await message.answer(signal)
    else:
        await message.answer("Не удалось получить сигнал. Попробуйте позже.")

@dp.message_handler(lambda message: message.text == "👁 Следить за монетой")
async def track_button(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        await message.answer(f"Начинаю следить за монетой {coin['id']} по цене {coin['price']} $")
        await start_tracking(bot, USER_ID, coin['id'], coin['price'])
    else:
        await message.answer("Монета не выбрана для отслеживания. Попробуйте позже.")

# --- Планировщик ---
async def scheduled_signal():
    coin = get_top_ton_wallet_coins()
    if coin:
        price = coin['price']
        goal_price = round(price * 1.05, 4)
        stop_price = round(price * 0.965, 4)
        signal = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10 + 50}%\n"
            f"🎯 Цель: {goal_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_price} $ (-3.5%)"
        )
        await bot.send_message(USER_ID, signal)

scheduler.add_job(scheduled_signal, trigger='cron', hour=8, minute=0, timezone='Europe/Moscow')

# --- Запуск ---
if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
