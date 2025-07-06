import logging
from aiogram import Bot, Dispatcher, executor, types
from config import TELEGRAM_TOKEN, OWNER_ID
from signal_utils import get_next_signal_message, reset_signal_index
from tracking import stop_all_trackings

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard())

@dp.message_handler(lambda message: message.text == "Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    try:
        signal_message, coin_id, entry_price = await get_next_signal_message()
        await message.answer(signal_message, reply_markup=signal_keyboard(coin_id, entry_price))
    except Exception as e:
        logging.error(f"Ошибка при получении сигнала: {e}")
        await message.answer("⚠️ Не удалось получить сигналы.")

@dp.message_handler(lambda message: message.text == "Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    stop_all_trackings()
    await message.answer("❌ Все отслеживания остановлены.")

@dp.message_handler(lambda message: message.text == "Старт")
async def handle_start_button(message: types.Message):
    await send_welcome(message)

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def handle_track_callback(callback_query: types.CallbackQuery):
    try:
        _, coin_id, entry_price = callback_query.data.split("_")
        from tracking import start_tracking
        await start_tracking(bot, coin_id, float(entry_price), OWNER_ID)
        await callback_query.answer("Монета добавлена в отслеживание.")
    except Exception as e:
        logging.error(f"Ошибка в callback track: {e}")
        await callback_query.answer("Ошибка при запуске отслеживания.")

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Получить ещё сигнал")
    keyboard.add("Остановить все отслеживания")
    keyboard.add("Старт")
    return keyboard

def signal_keyboard(coin_id, entry_price):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        text="Следить за монетой",
        callback_data=f"track_{coin_id}_{entry_price}"
    ))
    return keyboard

if __name__ == '__main__':
    logging.info("📡 Бот запущен и отслеживание активировано.")
    executor.start_polling(dp, skip_updates=True)
