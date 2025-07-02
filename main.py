import logging
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime, timedelta
import asyncio

from crypto_utils import get_top_ton_wallet_coins as analyze_tokens

# 🔐 Твой токен и ID
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
ADMIN_ID = 347552741

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Планировщик и часовой пояс
scheduler = AsyncIOScheduler()
moscow = timezone('Europe/Moscow')

# 👉 Кнопки
start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add("Получить ещё сигнал", "Следить за монетой")

# 📤 Функция отправки сигнала
async def send_signal(chat_id: int):
    try:
        coin = analyze_tokens()
        if coin:
            growth_prob = min(95, max(50, coin['score'] * 10))  # Пример вероятности
            msg = (
                f"📈 Монета: {coin['id'].upper()}\n"
                f"💵 Текущая цена: ${coin['price']}\n"
                f"📊 Изменение 24ч: {coin['change_24h']}%\n"
                f"📊 Изменение 7д: {coin['change_7d']}%\n"
                f"📈 Объём: ${coin['volume']:,}\n"
                f"🎯 Цель: +5%\n"
                f"📉 Стоп-лосс: -3%\n"
                f"📊 Вероятность роста: {growth_prob}%"
            )
        else:
            msg = "Не удалось проанализировать монеты."
        await bot.send_message(chat_id, msg)
    except Exception as e:
        logger.error(f"Ошибка в send_signal(): {e}")

# 🕗 Запуск по расписанию каждый день в 8:00 (МСК)
async def scheduled_signal():
    await send_signal(ADMIN_ID)

scheduler.add_job(
    scheduled_signal,
    trigger='cron',
    hour=8,
    minute=0,
    timezone=moscow
)

# 🟢 Команда /start и кнопка "Старт"
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("Добро пожаловать в новую жизнь, Корбан!", reply_markup=start_keyboard)

# ▶️ Кнопка «Получить ещё сигнал»
@dp.message_handler(lambda m: m.text == "Получить ещё сигнал")
async def handle_more_signal(message: types.Message):
    await send_signal(message.chat.id)

# 🧪 Команда для теста
@dp.message_handler(commands=["test"])
async def test_cmd(message: types.Message):
    await send_signal(message.chat.id)

# ▶️ Кнопка «Следить за монетой» (заглушка на будущее)
@dp.message_handler(lambda m: m.text == "Следить за монетой")
async def handle_follow(message: types.Message):
    await message.reply("🔜 Функция отслеживания монеты появится скоро!")

# 🚀 Старт
if __name__ == "__main__":
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
