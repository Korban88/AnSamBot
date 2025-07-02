import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import analyze_tokens, track_price_changes

# === Настройки ===
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

# === Клавиатура ===
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("🚀 Получить ещё сигнал"))
kb.add(KeyboardButton("🔔 Следить за монетой"))

# === Обработчики ===
@dp.message_handler(commands=["start"])
@dp.message_handler(lambda message: message.text == "Старт")
async def start(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=kb)

@dp.message_handler(commands=["test"])
async def test(message: types.Message):
    await send_signal(message.chat.id, test_mode=True)

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def handle_more_signal(message: types.Message):
    await send_signal(message.chat.id)

@dp.message_handler(lambda message: message.text == "🔔 Следить за монетой")
async def handle_follow(message: types.Message):
    result = analyze_tokens()
    if not result:
        await message.answer("Не удалось выбрать монету для отслеживания.")
        return

    token_id = result["id"]
    entry_price = result["price"]

    await message.answer(f"Начинаю отслеживать монету: {token_id.upper()}\nТекущая цена: ${entry_price}")
    asyncio.create_task(track_price_changes(bot, message.chat.id, token_id, entry_price))

# === Ежедневная задача ===
async def scheduled_signal():
    await send_signal(USER_ID)

scheduler.add_job(scheduled_signal, "cron", hour=8, minute=0)
scheduler.start()

# === Отправка сигнала ===
async def send_signal(chat_id, test_mode=False):
    try:
        result = analyze_tokens()
        if not result:
            await bot.send_message(chat_id, "\u26A0\ufe0f Монета не найдена. Попробуйте позже.")
            return

        msg = "\ud83d\udcc8 Сигнал на рост монеты:\n"
        if test_mode:
            msg = "\ud83d\udd8b\ufe0f Тестовый сигнал на основе анализа актуальных монет:\n"

        msg += (
            f"\nМонета: {result['id'].upper()}"
            f"\nЦена входа: ${result['price']}"
            f"\nЦель +5%: ${round(result['price'] * 1.05, 4)}"
            f"\nСтоп-лосс: ${round(result['price'] * 0.955, 4)}"
            f"\nИзменение за 24ч: {result['change_24h']}%"
            f"\nИзменение за 7д: {result['change_7d']}%"
            f"\nОбъём: ${result['volume']}"
        )

        await bot.send_message(chat_id, msg)

    except Exception as e:
        logging.error(f"Ошибка в send_signal(): {e}")
        await bot.send_message(chat_id, f"\u26A0\ufe0f Ошибка при анализе монет:\n{e}")

# === Запуск ===
if __name__ == "__main__":
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
