import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from tracker import CoinTracker
from signal_generator import generate_signal
from keyboard import main_keyboard

API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot)
tracker = CoinTracker(bot, USER_ID)
scheduler = AsyncIOScheduler()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_keyboard())

@dp.message_handler(lambda message: message.text == "📈 Получить ещё сигнал")
async def send_signals(message: types.Message):
    logger.info("Нажата кнопка 'Получить ещё сигнал'")
    result = await generate_signal()
    if result is None:
        await message.answer("⚠️ Сейчас нет подходящих монет. Но мы продолжаем искать!")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*
"
        f"Цена входа: `{result['entry_price']}`
"
        f"Цель (+5%): `{result['target_price']}`
"
        f"Стоп-лосс: `{result['stop_loss']}`
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"RSI: `{result['rsi']}` — {'перепродан' if result['rsi'] < 30 else 'перекуплен' if result['rsi'] > 70 else 'в норме'}
"
        f"MA7 > MA20: {'да' if result['ma7'] > result['ma20'] else 'нет'}"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="👁 Следить за монетой",
            callback_data=f"track:{result['symbol']}:{result['entry_price']}"
        )
    )

    await message.answer(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def handle_track_callback(callback_query: types.CallbackQuery):
    _, symbol, entry_price = callback_query.data.split(":")
    await tracker.start_tracking(symbol, float(entry_price))
    await callback_query.answer()
    await bot.send_message(USER_ID, f"🔔 Начал отслеживать {symbol.upper()} от {entry_price}")

@dp.message_handler(lambda message: message.text == "⛔ Остановить все отслеживания")
async def stop_tracking(message: types.Message):
    await tracker.stop_all()
    await message.answer("🛑 Все отслеживания остановлены.")

async def on_startup(dispatcher):
    scheduler.add_job(send_daily_signal, 'interval', days=1, start_date=datetime.now() + timedelta(seconds=10))
    scheduler.start()
    logger.info("⏳ До следующего сигнала: 1167.0 минут")

def send_daily_signal():
    asyncio.create_task(send_signal_now())

async def send_signal_now():
    result = await generate_signal()
    if result is None:
        await bot.send_message(USER_ID, "⚠️ Сегодня не удалось найти подходящую монету. Мы продолжаем мониторинг.")
        return

    text = (
        f"📊 *Утренний сигнал: {result['name']}*
"
        f"Цена входа: `{result['entry_price']}`
"
        f"Цель (+5%): `{result['target_price']}`
"
        f"Стоп-лосс: `{result['stop_loss']}`
"
        f"Вероятность роста: *{result['probability']}%*
"
        f"RSI: `{result['rsi']}` — {'перепродан' if result['rsi'] < 30 else 'перекуплен' if result['rsi'] > 70 else 'в норме'}
"
        f"MA7 > MA20: {'да' if result['ma7'] > result['ma20'] else 'нет'}"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="👁 Следить за монетой",
            callback_data=f"track:{result['symbol']}:{result['entry_price']}"
        )
    )

    await bot.send_message(USER_ID, text, reply_markup=keyboard)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
