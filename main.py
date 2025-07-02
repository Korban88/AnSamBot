import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from crypto_utils import get_top_ton_wallet_coins

# === НАСТРОЙКИ ===
BOT_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
OWNER_ID = 347552741

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracked_coin = None
tracked_data = {}

# === КНОПКИ ===
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Получить ещё сигнал", callback_data="get_signal"),
        InlineKeyboardButton("🔍 Следить за монетой", callback_data="track_coin")
    )
    return keyboard

# === АНАЛИЗ ===
async def send_signal():
    coin = get_top_ton_wallet_coins()
    if coin is None:
        await bot.send_message(OWNER_ID, "❌ Не удалось получить монету.")
        return

    message = (
        f"💰 Сигнал:
"
        f"Монета: {coin['id'].upper()}
"
        f"Цена: ${coin['price']}
"
        f"⬆️ 24ч: {coin['change_24h']}%
"
        f"📊 7д: {coin['change_7d']}%
"
        f"📈 Объём: {coin['volume']}
"
        f"🔢 Вероятность роста: {min(coin['score'] * 15, 95)}%"
    )

    await bot.send_message(OWNER_ID, message, reply_markup=get_main_keyboard())

# === КОМАНДЫ ===
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=get_main_keyboard())

@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    await message.answer("Тестовый сигнал:")
    await send_signal()

# === ОБРАБОТКА КНОПОК ===
@dp.callback_query_handler(lambda call: True)
async def handle_callback(call: types.CallbackQuery):
    if call.data == "get_signal":
        await bot.answer_callback_query(call.id)
        await send_signal()

    elif call.data == "track_coin":
        global tracked_coin, tracked_data
        coin = get_top_ton_wallet_coins()
        if coin is None:
            await call.message.answer("\u274C Монета для отслеживания не найдена.")
            return

        tracked_coin = coin['id']
        tracked_data = {
            'start_time': datetime.utcnow(),
            'start_price': coin['price']
        }

        await call.message.answer(f"⏱ Начал следить за {tracked_coin.upper()} — ${tracked_data['start_price']}")
        await bot.answer_callback_query(call.id)

# === ПРОВЕРКА ОТСЛЕЖИВАНИЯ ===
async def check_tracking():
    global tracked_coin, tracked_data
    if not tracked_coin:
        return

    now = datetime.utcnow()
    coin = get_top_ton_wallet_coins()
    if not coin or coin['id'] != tracked_coin:
        return

    current_price = coin['price']
    start_price = tracked_data['start_price']
    change_percent = round((current_price - start_price) / start_price * 100, 2)
    time_diff = now - tracked_data['start_time']

    if change_percent >= 5:
        await bot.send_message(OWNER_ID, f"🎉 {tracked_coin.upper()} вырос на {change_percent}%! (${start_price} ➔ ${current_price})")
        tracked_coin = None
    elif time_diff >= timedelta(hours=12):
        trend = "выросла" if change_percent > 0 else "упала"
        await bot.send_message(OWNER_ID, f"⏱ 12 часов прошло. {tracked_coin.upper()} {trend} на {change_percent}% (${start_price} ➔ ${current_price})")
        tracked_coin = None
    elif change_percent >= 3.5:
        await bot.send_message(OWNER_ID, f"⬆️ {tracked_coin.upper()} вырос на 3.5%+ (${start_price} ➔ ${current_price})")

# === ПЛАНИРОВЩИК ===
scheduler.add_job(send_signal, trigger='cron', hour=5, minute=0)  # 8:00 МСК
scheduler.add_job(check_tracking, trigger='interval', minutes=10)
scheduler.start()

# === ЗАПУСК ===
if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
