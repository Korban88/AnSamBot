import logging
from aiogram import Bot, Dispatcher, executor, types
from config import TELEGRAM_TOKEN, OWNER_ID
from keyboards import main_keyboard
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import start_tracking

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard(), parse_mode=None)

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    try:
        signal_message, coin_id, entry_price = await get_next_signal_message()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{coin_id}:{entry_price}"))
        await message.answer(signal_message, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка при получении сигнала: {e}")
        await message.answer("⚠️ Не удалось получить сигналы.")

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    reset_signal_index()
    await message.answer("⛔️ Все отслеживания остановлены.")

@dp.callback_query_handler(lambda c: c.data.startswith("track:"))
async def handle_tracking_callback(callback_query: types.CallbackQuery):
    _, coin_id, entry_price = callback_query.data.split(":")
    await start_tracking(bot, callback_query.from_user.id, coin_id, float(entry_price))
    await callback_query.answer("🔔 Отслеживание запущено!")

if __name__ == "__main__":
    logging.info("📡 Бот запущен и отслеживание активировано.")
    executor.start_polling(dp, skip_updates=True)
