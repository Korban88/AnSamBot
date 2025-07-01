import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import analyze_tokens
import os

# Вставь сюда свой токен
BOT_TOKEN = os.getenv("8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# ======= КНОПКИ =======
start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(KeyboardButton("Старт"))
start_kb.add(KeyboardButton("🚀 Получить ещё сигнал"))

# ======= ГЛАВНАЯ ФУНКЦИЯ =======
async def send_signal(chat_id):
    try:
        result = analyze_tokens()
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

# ======= КОМАНДА /start =======
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=start_kb)

# ======= КОМАНДА /test =======
@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    await message.answer("🧪 Тестовый сигнал на основе анализа актуальных монет:")
    await send_signal(message.chat.id)

# ======= КНОПКА "Старт" =======
@dp.message_handler(lambda message: message.text == "Старт")
async def handle_start_button(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")

# ======= КНОПКА "Получить ещё сигнал" =======
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def handle_signal_button(message: types.Message):
    await send_signal(message.chat.id)

# ======= ЕЖЕДНЕВНЫЙ СИГНАЛ =======
async def scheduled_signal():
