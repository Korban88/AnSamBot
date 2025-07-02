import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import get_top_ton_wallet_coins  # Удалили track_price_changes

# Конфигурация
BOT_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
USER_ID = 347552741
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

# Хранилище отслеживаемых монет
tracked_coin = None
tracked_price = None
tracking_start_time = None

# Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("🔔 Следить за монетой"))

# Обработчики
@dp.message_handler(commands=['start'])
@dp.message_handler(lambda message: message.text == "Старт")
async def start_command(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=keyboard)

@dp.message_handler(commands=['test'])
@dp.message_handler(lambda message: message.text == "🚀 Получить ещё сигнал")
async def send_signal(message: types.Message):
    try:
        result = get_top_ton_wallet_coins()
        if result:
            signal_text = format_signal(result)
            await message.answer(signal_text)
        else:
            await message.answer("Ошибка: не удалось получить данные по монетам.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при анализе монет: {e}")

@dp.message_handler(lambda message: message.text == "🔔 Следить за монетой")
async def follow_coin(message: types.Message):
    global tracked_coin, tracked_price, tracking_start_time
    try:
        result = get_top_ton_wallet_coins()
        if result:
            tracked_coin = result['name']
            tracked_price = result['price']
            tracking_start_time = asyncio.get_event_loop().time()
            await message.answer(f"🔔 Теперь отслеживаем {tracked_coin} по цене ${tracked_price:.4f}")
        else:
            await message.answer("Ошибка: не удалось получить данные по монетам.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при запуске отслеживания: {e}")

async def scheduled_signal():
    try:
        result = get_top_ton_wallet_coins()
        if result:
            signal_text = format_signal(result)
            await bot.send_message(USER_ID, signal_text)
    except Exception as e:
        logging.error(f"Ошибка в scheduled_signal: {e}")

async def track_coin_changes():
    global tracked_coin, tracked_price, tracking_start_time
    if not tracked_coin or not tracked_price:
        return

    try:
        result = get_top_ton_wallet_coins()
        if result and result['name'] == tracked_coin:
            current_price = result['price']
            change_percent = ((current_price - tracked_price) / tracked_price) * 100
            elapsed = asyncio.get_event_loop().time() - tracking_start_time

            if change_percent >= 5:
                await bot.send_message(USER_ID, f"📈 {tracked_coin} вырос на +5%! Цена: ${current_price:.4f}")
                tracked_coin = None  # сброс отслеживания
            elif change_percent >= 3.5:
                await bot.send_message(USER_ID, f"📈 {tracked_coin} вырос на +3.5%. Цена: ${current_price:.4f}")
            elif elapsed >= 43200:
                await bot.send_message(USER_ID, f"⏳ {tracked_coin} не вырос на 3.5% за 12 часов.")
                tracked_coin = None

    except Exception as e:
        logging.error(f"Ошибка при отслеживании монеты: {e}")

# Форматирование сигнала

def format_signal(data):
    name = data['name']
    price = data['price']
    change_24h = data.get('change_24h', 0)
    change_7d = data.get('change_7d', 0)
    volume = data.get('volume', 0)
    target = price * 1.05
    stop = price * 0.95
    return (
        f"📈 Сигнал на рост монеты:\n"
        f"Монета: {name}\n"
        f"Цена входа: ${price:.4f}\n"
        f"Цель +5%: ${target:.4f}\n"
        f"Стоп-лосс: ${stop:.4f}\n"
        f"Изменение за 24ч: {change_24h:.2f}%\n"
        f"Изменение за 7д: {change_7d:.2f}%\n"
        f"Объём: ${volume}"
    )

async def scheduler_loop():
    scheduler.add_job(scheduled_signal, 'cron', hour=8, minute=0)
    scheduler.add_job(track_coin_changes, 'interval', minutes=10)
    scheduler.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop())
    executor.start_polling(dp, skip_updates=True)
