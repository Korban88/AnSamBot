import logging
import re
from types import SimpleNamespace
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config import TELEGRAM_TOKEN, USER_ID
from analysis import analyze_cryptos
from tracking import CoinTracker, CoinTrackingManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Функция экранирования MarkdownV2
def escape_markdown(text):
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

# Постоянная клавиатура: 🏁 сверху, остальные ниже
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🏁 Старт"))
keyboard.row(
    KeyboardButton("📊 Получить ещё сигнал"),
    KeyboardButton("🛑 Остановить все отслеживания"),
)

# Хранилище топ-3 монет для последовательного показа
top3_cache = []
top3_index = 0

# Команда /start или кнопка Старт
@dp.message_handler(commands=["start"])
@dp.message_handler(lambda message: message.text == "🏁 Старт")
async def handle_start_command(message: types.Message):
    text = (
        "Добро пожаловать в новую жизнь, Корбан!\n\n"
        "Бот готов присылать крипто-сигналы с высоким потенциалом роста."
    )
    await message.answer(escape_markdown(text), reply_markup=keyboard)

# Кнопка: Получить ещё сигнал
@dp.message_handler(lambda message: message.text == "📊 Получить ещё сигнал")
async def handle_get_signal(message: types.Message):
    global top3_cache, top3_index
    logger.info("⚡ Обработка сигнала запущена")
    if not top3_cache or top3_index >= len(top3_cache):
        top3_cache = await analyze_cryptos()
        top3_index = 0

    if not top3_cache:
        await message.answer("❌ Топ-3 монет не найден")
        return

    coin_data = top3_cache[top3_index]
    top3_index += 1

    text = (
        f"📈 *Сигнал по монете: {coin_data['name'].upper()}*\n"
        f"🔮 Вероятность роста: *{coin_data['growth_probability']}%*\n"
        f"🎯 Цена входа: {coin_data['price']} USD\n"
        f"🎯 Цель: {coin_data['target_price']} USD (+5%)\n"
        f"🛡️ Стоп-лосс: {coin_data['stop_loss']} USD (-3%)"
    )

    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track:{coin_data['name']}"))

    await message.answer(escape_markdown(text), reply_markup=inline_kb)

# Обработка нажатия кнопки следить за монетой
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("track:"))
async def process_tracking_callback(callback_query: types.CallbackQuery):
    coin_name = callback_query.data.split(":")[1]
    CoinTracker.track_coin(coin_name, USER_ID)
    await bot.answer_callback_query(callback_query.id, text=f"Начато отслеживание {coin_name.upper()}")
    await bot.send_message(USER_ID, f"🔔 Теперь отслеживается монета {coin_name.upper()} (+3.5%, +5%, 12ч)")

# Кнопка: Остановить все отслеживания
@dp.message_handler(lambda message: message.text == "🛑 Остановить все отслеживания")
async def handle_stop_tracking(message: types.Message):
    CoinTracker.clear_all()
    await message.answer("🔕 Все отслеживания остановлены.")

# Планировщик задач
scheduler.add_job(
    handle_get_signal,
    CronTrigger(hour=8, minute=0),
    args=[SimpleNamespace(text="📊 Получить ещё сигнал", chat=SimpleNamespace(id=USER_ID))],
    id="daily_signal"
)

tracking_manager = CoinTrackingManager()
scheduler.add_job(tracking_manager.run, IntervalTrigger(minutes=10))

scheduler.start()

if __name__ == '__main__':
    logger.info("✅ Бот готов к работе.")
    executor.start_polling(dp, skip_updates=True)
