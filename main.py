import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from analysis import analyze_cryptos
from signal_utils import get_next_signal_message, reset_signal_index
from config import TELEGRAM_TOKEN, OWNER_ID

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание экземпляра бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# ==== КНОПКИ ====
start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📈 Получить ещё сигнал", callback_data="get_another_signal")]
])

# ==== ОБРАБОТЧИКИ ====
@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=start_keyboard)
    reset_signal_index(message.from_user.id)

@dp.callback_query_handler(lambda c: c.data == "get_another_signal")
async def handle_get_another_signal(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    try:
        top_cryptos = await analyze_cryptos()

        if not top_cryptos:
            await bot.send_message(user_id, "❌ Не удалось подобрать монеты. Попробуй позже.")
            return

        signal = get_next_signal_message(user_id, top_cryptos)

        if signal:
            await bot.send_message(user_id, signal["text"], reply_markup=signal["keyboard"], parse_mode="MarkdownV2")
        else:
            await bot.send_message(user_id, "✅ Все сигналы уже были показаны. Попробуй позже.")

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации сигнала: {e}")
        await bot.send_message(user_id, "🚫 Ошибка при обработке сигнала.")

# ==== ЗАПУСК ====
if __name__ == "__main__":
    logger.info("🚀 Бот запущен")
    executor.start_polling(dp, skip_updates=True)
