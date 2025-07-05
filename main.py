import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN, TELEGRAM_ID
from analysis import get_top_signals
from tracking import CoinTracker

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)

# Постоянная клавиатура (внизу)
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("🟢 Старт"), KeyboardButton("🚀 Получить ещё сигнал"))
main_keyboard.add(KeyboardButton("🛑 Остановить все отслеживания"))

# Inline клавиатура (под сообщением)
def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔍 Следить за монетой", callback_data="track"),
        InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="more"),
        InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking"),
    )
    return keyboard

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Добро пожаловать в новую жизнь, Корбан\\!\n\nБот готов к работе\\.",
        reply_markup=main_keyboard
    )

@dp.message_handler(lambda message: message.text == "🟢 Старт")
async def handle_start(message: types.Message):
    await message.answer("✅ Бот активирован", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def handle_more(message: types.Message):
    await send_signal(message.chat.id)

@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    CoinTracker.stop_all()
    await message.answer("❌ Все отслеживания остановлены.", reply_markup=main_keyboard)

@dp.callback_query_handler(lambda c: c.data == "more")
async def more_signal(callback_query: types.CallbackQuery):
    await send_signal(callback_query.from_user.id)

@dp.callback_query_handler(lambda c: c.data == "track")
async def track_signal(callback_query: types.CallbackQuery):
    CoinTracker.track_current()
    await callback_query.answer("📡 Монета добавлена на отслеживание.")

@dp.callback_query_handler(lambda c: c.data == "stop_tracking")
async def stop_signal(callback_query: types.CallbackQuery):
    CoinTracker.stop_all()
    await callback_query.answer("🛑 Отслеживания остановлены.")

async def send_signal(chat_id):
    signal = get_top_signals(1)[0]

    symbol = signal.get("symbol", "—")
    price = signal.get("price", 0)
    target = signal.get("target", 0)
    stop_loss = signal.get("stop_loss", 0)
    probability = signal.get("probability", 0)

    # Проверка пустых значений
    if price == 0 or symbol == "—":
        await bot.send_message(chat_id, "⚠️ Нет актуальных данных для монеты.")
        return

    # Экранируем MarkdownV2
    def esc(text):
        return str(text).replace("-", "\\-").replace(".", "\\.").replace("!", "\\!").replace("(", "\\(").replace(")", "\\)").replace("+", "\\+")

    text = (
        f"📈 *Сигнал по монете:* {esc(symbol)}\n\n"
        f"💎 Текущая цена: \\${esc(price)}\n"
        f"🎯 Цель \\(\\+5%\\): \\${esc(target)}\n"
        f"🛑 Стоп\\-лосс \\(\\-3%\\): \\${esc(stop_loss)}\n"
        f"📊 Вероятность роста: *{esc(probability)}%*"
    )

    await bot.send_message(chat_id, text, reply_markup=get_inline_keyboard())

# Планировщик
scheduler = AsyncIOScheduler()

def daily_signal():
    asyncio.create_task(send_signal(TELEGRAM_ID))

scheduler.add_job(daily_signal, "cron", hour=8, minute=0)
scheduler.add_job(CoinTracker.run, "interval", minutes=10)
scheduler.start()

if __name__ == "__main__":
    logger.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
