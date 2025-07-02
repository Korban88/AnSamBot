import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import get_top_ton_wallet_coins
from tracking import start_tracking

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Получить ещё сигнал"))
keyboard.add(KeyboardButton("Следить за монетой"))

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=keyboard)

# Обработка кнопки «Получить ещё сигнал»
@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def get_extra_signal(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        text = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {coin['price']} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10}%\n"
            f"🎯 Цель: +5%\n"
            f"⛔️ Стоп-лосс: -3%"
        )
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("Не удалось получить данные по монетам.")

# Обработка кнопки «Следить за монетой»
@dp.message_handler(lambda message: message.text == "Следить за монетой")
async def track_coin(message: types.Message):
    coin = get_top_ton_wallet_coins()
    if coin:
        await message.answer(f"Начинаю отслеживать {coin['id']} с цены {coin['price']} $ на 12 часов...")
        await start_tracking(message, coin['id'], coin['price'])
    else:
        await message.answer("Не удалось выбрать монету для отслеживания.")

# Автосигнал каждый день в 8:00
async def scheduled_signal():
    coin = get_top_ton_wallet_coins()
    if coin:
        text = (
            f"💰 Сигнал:\n"
            f"Монета: {coin['id']}\n"
            f"Цена: {coin['price']} $\n"
            f"Рост за 24ч: {coin['change_24h']}%\n"
            f"Вероятность роста: {coin['score'] * 10}%\n"
            f"🎯 Цель: +5%\n"
            f"⛔️ Стоп-лосс: -3%"
        )
        await bot.send_message(USER_ID, text)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.loop.create_task(scheduler.start())
    scheduler.add_job(scheduled_signal, "cron", hour=8, minute=0)
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
