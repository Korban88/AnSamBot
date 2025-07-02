import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from crypto_utils import get_top_ton_wallet_coins
from tracking import start_tracking

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Получить ещё сигнал"))
keyboard.add(KeyboardButton("Следить за монетой"))

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def more_signal(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        msg = f"""💰 Сигнал:

Монета: {coin['id']}
Цена входа: ${coin['price']}
Изменение за 24ч: {coin['change_24h']}%
Изменение за 7д: {coin['change_7d']}%
Объём: ${coin['volume']}
Цель: +5% -> ${round(coin['price'] * 1.05, 4)}
Стоп-лосс: ${round(coin['price'] * 0.965, 4)}
Вероятность роста: {round(min(97, coin['score'] * 12 + 40), 1)}%
"""
        await message.answer(msg)
    else:
        await message.answer("Не удалось получить данные. Попробуйте позже.")

@dp.message_handler(lambda message: message.text == "Следить за монетой")
async def track_coin(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        await message.answer(f"Запускаю отслеживание монеты {coin['id']} по цене ${coin['price']}.")
        await start_tracking(bot, USER_ID, coin)
    else:
        await message.answer("Не удалось выбрать монету для отслеживания.")

async def scheduled_signal():
    coin = get_top_ton_wallet_coins()
    if coin:
        msg = f"""💰 Сигнал:

Монета: {coin['id']}
Цена входа: ${coin['price']}
Изменение за 24ч: {coin['change_24h']}%
Изменение за 7д: {coin['change_7d']}%
Объём: ${coin['volume']}
Цель: +5% -> ${round(coin['price'] * 1.05, 4)}
Стоп-лосс: ${round(coin['price'] * 0.965, 4)}
Вероятность роста: {round(min(97, coin['score'] * 12 + 40), 1)}%
"""
        await bot.send_message(USER_ID, msg)

async def on_startup(_):
    logging.info("Бот запущен и готов к работе.")
    scheduler.add_job(scheduled_signal, 'cron', hour=8, minute=0)
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
