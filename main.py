import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio
from crypto_utils import get_top_ton_wallet_coins

API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
ADMIN_ID = 347552741

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Хранилище отслеживаемых монет
tracked_coins = {}

# Кнопки
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Получить ещё сигнал"), KeyboardButton("Следить за монетой"))

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать в AnSam Bot!", reply_markup=main_kb)

@dp.message_handler(commands=['test'])
async def test_cmd(message: types.Message):
    await send_signal(message.chat.id)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def get_signal(message: types.Message):
    await send_signal(message.chat.id)

@dp.message_handler(lambda message: message.text == "Следить за монетой")
async def follow_coin(message: types.Message):
    coin = await get_top_ton_wallet_coins()
    if coin:
        coin_id = coin['id']
        tracked_coins[coin_id] = {
            'start_price': coin['price'],
            'start_time': datetime.now(),
            'user_id': message.chat.id
        }
        await message.answer(f"Начинаю отслеживать монету {coin_id.upper()} по цене {coin['price']} USD")
    else:
        await message.answer("Не удалось начать отслеживание монеты.")

async def send_signal(chat_id):
    coin = await get_top_ton_wallet_coins()
    if coin:
        probability = min(95, max(50, coin['score'] * 15))
        text = (
            f"🔥 Сигнал на рост монеты: {coin['id'].upper()}\n"
            f"Текущая цена: {coin['price']} USD\n"
            f"Изменение за 24ч: {coin['change_24h']}%\n"
            f"Изменение за 7д: {coin['change_7d']}%\n"
            f"Объём: {coin['volume']} USD\n"
            f"🎯 Цель: +5%\n"
            f"🔐 Вероятность роста: {probability}%"
        )
        await bot.send_message(chat_id, text, reply_markup=main_kb)
    else:
        await bot.send_message(chat_id, "Не удалось получить сигнал.", reply_markup=main_kb)

async def check_tracked_coins():
    now = datetime.now()
    for coin_id, data in list(tracked_coins.items()):
        try:
            user_id = data['user_id']
            start_price = data['start_price']
            start_time = data['start_time']
            current_data = await get_top_ton_wallet_coins()

            if not current_data or current_data['id'] != coin_id:
                continue

            current_price = current_data['price']
            change = ((current_price - start_price) / start_price) * 100

            if change >= 5:
                await bot.send_message(user_id, f"🚀 Монета {coin_id.upper()} выросла на +5% с момента отслеживания! Цена: {current_price} USD")
                tracked_coins.pop(coin_id)
            elif now - start_time >= timedelta(hours=12):
                direction = "выросла" if change > 0 else "упала"
                await bot.send_message(user_id, f"⌛ 12 часов прошло. Монета {coin_id.upper()} {direction} на {round(abs(change), 2)}%. Отслеживание завершено.")
                tracked_coins.pop(coin_id)
            elif change >= 3.5:
                await bot.send_message(user_id, f"📈 Монета {coin_id.upper()} выросла на +3.5%! Текущая цена: {current_price} USD")
        except Exception as e:
            logging.error(f"Ошибка при проверке монеты {coin_id}: {e}")

async def scheduled_signal():
    await send_signal(ADMIN_ID)

async def scheduler_task():
    while True:
        await check_tracked_coins()
        await asyncio.sleep(600)  # каждые 10 минут

async def on_startup(_):
    scheduler.add_job(scheduled_signal, 'cron', hour=8, minute=0)
    scheduler.start()
    asyncio.create_task(scheduler_task())
    logging.info("Бот запущен и готов к работе.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
