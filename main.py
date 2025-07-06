import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import tracking_loop
from utils import escape_markdown

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем бота и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

# Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Получить ещё сигнал"))
keyboard.add(KeyboardButton("Остановить все отслеживания"))
keyboard.add(KeyboardButton("Старт"))


@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.answer(escape_markdown("Добро пожаловать в новую жизнь, Корбан!"), reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    signal_message, coin_id, entry_price = await get_next_signal_message()
    await message.answer(escape_markdown(signal_message), reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_reset_signal_index(message: types.Message):
    reset_signal_index()
    await message.answer(escape_markdown("♻️ Индекс сигналов сброшен. Теперь сигналы пойдут сначала."), reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Старт")
async def handle_start_button(message: types.Message):
    await handle_start(message)


if __name__ == "__main__":
    logger.info("📡 Бот запущен и отслеживание активировано.")

    # Запускаем фоновую задачу
    async def on_startup(dispatcher):
        asyncio.create_task(tracking_loop(bot))

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
