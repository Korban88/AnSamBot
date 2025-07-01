import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime
import asyncio
from crypto_utils import get_top_ton_wallet_coins as analyze_tokens

# Вставь свой токен
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(level=logging.INFO)

# Планировщик и таймзона
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# Кнопки
start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add(KeyboardButton("Старт"))
start_keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))

# 🔧 Функция отправки сигнала
async def send_signal(chat_id):
    try:
        result = analyze_tokens()
        logging.info(f"Результат анализа: {result}")

        if not result:
            await bot.send_message(chat_id, "⚠️ Не удалось найти перспективную монету.")
            return

        msg = (
            f"📈 *Сигнал на рост монеты:*\n\n"
            f"*Монета:* `{result['id'].upper()}`\n"
            f"*Цена входа:* `${result['price']}`\n"
            f"*Цель +5%:* `${round(result['price'] * 1.05, 4)}`\n"
            f"*Стоп-лосс:* `${round(result['price'] * 0.96, 4)}`\n"
            f"*Изменение за 24ч:* `{result['change_24h']}%`\n"
            f"*Изменение за 7д:* `{result['change_7d']}%`\n"
            f"*Объём:* `${result['volume']}`"
        )
        await bot.send_message(chat_id, msg, parse_mode="Markdown")
    except Exception as e:
        logging.exception("Ошибка в send_signal()")
        await bot.send_message(chat_id, f"⚠️ Ошибка при анализе монет:\n{str(e)}")

# 🕗 Плановый сигнал каждый день в 8:00 МСК
async def scheduled_signal():
    await send_signal(chat_id=347552741)  # замени на свой ID при необходимости

scheduler.add_job(
    scheduled_signal,
    trigger='cron',
    hour=8,
    minute=0,
    timezone=moscow
)

# 📩 Обработка команды /start и кнопки Старт
@dp.message_handler(commands=['start'])
@dp.message_handler(lambda message: message.text.lower() == "старт")
async def start_handler(message: types.Message):
    await message.reply("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=start_keyboard)

# 🚀 Обработка кнопки "Получить ещё сигнал"
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def more_signal_handler(message: types.Message):
    await send_signal(message.chat.id)

# 🧪 Тестовая команда
@dp.message_handler(commands=['test'])
async def test_handler(message: types.Message):
    await message.reply("✏️ Тестовый сигнал на основе анализа актуальных монет:")
    await send_signal(message.chat.id)

# 🔁 Запуск
if __name__ == '__main__':
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
