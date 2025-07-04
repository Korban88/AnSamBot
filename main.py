import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from apscheduler.schedulers.background import BackgroundScheduler
from signal_generator import generate_signal
from tracker import CoinTracker
from config import BOT_TOKEN, USER_ID
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
tracker = CoinTracker(bot, USER_ID)

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("📈 Получить ещё сигнал"),
    KeyboardButton("🛑 Остановить все отслеживания")
)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!\n\nБот готов выдавать тебе сильнейшие сигналы каждый день в 08:00 по Москве.", reply_markup=main_menu)

@dp.message_handler(Text(equals="📈 Получить ещё сигнал"))
async def handle_get_signal(message: types.Message):
    result = generate_signal()
    if result is None:
        await message.answer("⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"*Цена входа:* {result['entry_price']}\n"
        f"*Цель +5%:* {result['target_price']}\n"
        f"*Стоп-лосс:* {result['stop_loss']}\n"
        f"*Вероятность роста:* {result['probability']}%\n\n"
        f"*Объяснение:*\n"
        f"RSI: {result['rsi']}, Объём: {result['volume']} USDT\n"
        f"Тренд: {result['trend']}, 24ч: {result['change_24h']}%"
    )

    # Кнопка отслеживания монеты
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{result['symbol']}")
    )

    await message.answer(text, reply_markup=markup)

@dp.message_handler(Text(equals="🛑 Остановить все отслеживания"))
async def handle_stop_tracking(message: types.Message):
    tracker.clear_all()
    await message.answer("❌ Все отслеживания остановлены.")

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def handle_track_callback(callback_query: types.CallbackQuery):
    symbol = callback_query.data.split("_", 1)[1]
    tracker.track(symbol)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"🔔 Монета {symbol} отслеживается. Уведомлю при росте +3.5% или +5%.")

async def send_daily_signal():
    result = generate_signal()
    if result is None:
        await bot.send_message(USER_ID, "⚠️ Утром не нашлось сильной монеты для сигнала. Повторите позже.")
        return

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"*Цена входа:* {result['entry_price']}\n"
        f"*Цель +5%:* {result['target_price']}\n"
        f"*Стоп-лосс:* {result['stop_loss']}\n"
        f"*Вероятность роста:* {result['probability']}%\n\n"
        f"*Объяснение:*\n"
        f"RSI: {result['rsi']}, Объём: {result['volume']} USDT\n"
        f"Тренд: {result['trend']}, 24ч: {result['change_24h']}%"
    )

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{result['symbol']}")
    )

    await bot.send_message(USER_ID, text, reply_markup=markup)

# Планировщик
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
scheduler.start()

async def on_startup(dp):
    logger.info(f"⏳ До следующего сигнала: {minutes_until_8am()} минут")
    logger.info("✅ Бот готов к работе.")

def minutes_until_8am():
    now = datetime.datetime.now()
    next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= next_8am:
        next_8am += datetime.timedelta(days=1)
    return int((next_8am - now).total_seconds() // 60)

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
