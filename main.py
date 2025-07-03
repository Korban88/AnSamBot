import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from crypto_utils import get_top_coins
from tracking import CoinTracker
import logging

# Токен твоего бота
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)
tracker = CoinTracker()

# Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("👁 Следить за монетой"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

# Кнопка Старт
@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")

# Кнопка Получить ещё сигнал
@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_signals(message: types.Message):
    coins = get_top_coins()
    if not coins:
        await message.answer("Не удалось получить сигналы. Попробуйте позже.")
        return

    for coin in coins:
        try:
            name = coin['id']
            price = coin['price']
            change = coin['change_24h']
            probability = coin['probability']
            target_price = coin['target_price']
            stop_loss_price = coin['stop_loss_price']

            text = (
                f"💰 *Сигнал:*\n"
                f"Монета: {name}\n"
                f"Цена: *{price} $*\n"
                f"Рост за 24ч: {change}%\n"
                f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: {probability}%\n"
                f"🎯 Цель: *{target_price} $* \\(+5%\\)\n"
                f"⛔️ Стоп-лосс: {stop_loss_price} $ \\(-3\\.5%\\)"
            )

            await message.answer(text)

        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {e}")

# Кнопка Остановить все отслеживания
@dp.message_handler(Text(equals="🔴 Остановить все отслеживания"))
async def stop_tracking(message: types.Message):
    tracker.clear_tracking()
    await message.answer("Все отслеживания монет остановлены.")

# Кнопка Следить за монетой (заглушка)
@dp.message_handler(Text(equals="👁 Следить за монетой"))
async def track_coin(message: types.Message):
    await message.answer("⚙️ В разработке: интеллектуальное отслеживание монет.")

# Запуск
if __name__ == '__main__':
    from scheduler import schedule_daily_signal
    schedule_daily_signal(dp, bot, get_top_coins)
    executor.start_polling(dp, skip_updates=True)
