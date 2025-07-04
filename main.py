import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from config import BOT_TOKEN, USER_ID
from signal_generator import generate_signal
from coin_tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

tracker = CoinTracker()

# Кнопки управления
main_keyboard = InlineKeyboardMarkup(row_width=2)
main_keyboard.add(
    InlineKeyboardButton("📈 Получить ещё сигнал", callback_data="more_signal"),
    InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")
)

# Обработка команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if message.chat.id != USER_ID:
        return
    await message.answer("AnSam Bot запущен. Готов к прибыли!", reply_markup=main_keyboard)

# Генерация сигнала и кнопки отслеживания
async def send_signal():
    result = generate_signal()
    if result is None:
        await bot.send_message(USER_ID, "⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    signal_text = (
        f"💡 *Сигнал на рост: {result['name']} ({result['symbol']})*\n"
        f"Цена входа: `${result['entry']}`\n"
        f"Цель +5%: `${result['target']}`\n"
        f"Стоп-лосс: `${result['stop']}`\n\n"
        f"Вероятность роста: *{result['probability']}%*\n"
        f"Изменение за 24ч: `{result['change_24h']:.2f}%`\n"
        f"RSI: `{result['rsi']}`, MA7: `{result['ma7']}`, MA20: `{result['ma20']}`"
    )

    track_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f"🔔 Следить за {result['symbol'].upper()}", callback_data=f"track:{result['symbol']}")
    )

    await bot.send_message(USER_ID, signal_text, reply_markup=track_button)

# Обработка кнопки "Получить ещё сигнал"
@dp.callback_query_handler(lambda c: c.data == "more_signal")
async def handle_more_signal(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await send_signal()

# Обработка кнопки "Остановить все отслеживания"
@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_tracking(callback_query: types.CallbackQuery):
    await callback_query.answer("Все отслеживания остановлены")
    tracker.stop_all()

# Обработка кнопки отслеживания монеты
@dp.callback_query_handler(lambda c: c.data.startswith("track:"))
async def track_coin(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split(":")[1]
    await callback_query.answer(f"Теперь отслеживаем {symbol.upper()}")
    tracker.track_coin(symbol, USER_ID)

# Планировщик ежедневного сигнала в 8:00 МСК
async def send_daily_signal():
    now = datetime.utcnow() + timedelta(hours=3)  # МСК
    logger.info(f"⏳ До следующего сигнала: {(24*60 - now.hour*60 - now.minute)} минут")
    await send_signal()

# Старт
async def on_startup(dp):
    logger.info("✅ Бот готов к работе.")
    scheduler.add_job(send_daily_signal, 'cron', hour=8, minute=0)
    scheduler.start()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
