import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import analyze_tokens
import asyncio

# 🔐 Токен и ID
BOT_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
USER_ID = 347552741

# 🤖 Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# 📦 Словарь отслеживаемых монет
watched_tokens = {}  # user_id: {'token': 'arbitrum', 'start_price': 1.12}

# 🎛️ Кнопки
keyboard = InlineKeyboardMarkup(row_width=1)
keyboard.add(
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more_signal"),
    InlineKeyboardButton("🔔 Следить за монетой", callback_data="watch_token")
)


# 🧠 Формула вероятности роста
def calculate_growth_probability(coin):
    score = coin["score"]
    prob = min(95, max(50, 65 + score * 5))  # простая формула на базе score
    return prob


# 📬 Отправка сигнала
async def send_signal(chat_id):
    try:
        result = analyze_tokens()
        if not result:
            await bot.send_message(chat_id, "⚠️ Не удалось получить данные для сигнала.")
            return

        prob = calculate_growth_probability(result)
        message = (
            f"📡 Сигнал на рост:\n\n"
            f"🔹 Монета: {result['id']}\n"
            f"💵 Цена: ${result['price']}\n"
            f"📈 24ч: {result['change_24h']}%\n"
            f"📊 7д: {result['change_7d']}%\n"
            f"💰 Объём: ${result['volume']}\n"
            f"📊 Вероятность роста: {prob}%\n\n"
            f"🎯 Цель: +5%\n⛔️ Стоп-лосс: -3%"
        )

        await bot.send_message(chat_id, message, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка в send_signal(): {e}")
        await bot.send_message(chat_id, f"⚠️ Ошибка при анализе монет:\n{e}")


# ⏰ Утренний сигнал
async def scheduled_signal():
    await send_signal(USER_ID)


# 📥 Команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Бот активен. Сигналы приходят в 8:00 по МСК.", reply_markup=keyboard)


# 🧪 Команда /test
@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    await message.answer("✏️ Тестовый сигнал:")
    await send_signal(message.chat.id)


# 🧲 Обработка кнопок
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if callback_query.data == "more_signal":
        await send_signal(callback_query.message.chat.id)

    elif callback_query.data == "watch_token":
        result = analyze_tokens()
        if result:
            watched_tokens[user_id] = {
                "token": result["id"],
                "start_price": result["price"]
            }
            await bot.send_message(user_id, f"🔔 Следим за {result['id']} от ${result['price']}. Уведомлю при +3.5%.")

        else:
            await bot.send_message(user_id, "⚠️ Монета не найдена.")


# 🔁 Проверка роста отслеживаемых монет
async def check_watched_tokens():
    for user_id, token_data in list(watched_tokens.items()):
        token = token_data["token"]
        start_price = token_data["start_price"]

        result = analyze_tokens()
        if result and result["id"] == token:
            current_price = result["price"]
            if current_price >= start_price * 1.035:
                await bot.send_message(
                    user_id,
                    f"🚀 {token} вырос на 3.5%!\n💰 Сейчас: ${current_price}"
                )
                del watched_tokens[user_id]


# ▶️ Запуск
if __name__ == '__main__':
    scheduler.add_job(scheduled_signal, trigger='cron', hour=8, minute=0)
    scheduler.add_job(check_watched_tokens, trigger='interval', minutes=10)
    scheduler.start()
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
