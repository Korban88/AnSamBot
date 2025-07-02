import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import get_top_ton_wallet_coins, track_price_changes

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

watchlist = {}

# Клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("🔔 Следить за монетой"))

# Старт
@dp.message_handler(lambda message: message.text.lower() == "старт")
async def start(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.", reply_markup=keyboard)

# Выдать сигнал
async def send_signal():
    try:
        result = get_top_ton_wallet_coins()
        if result is None:
            await bot.send_message(USER_ID, "⚠️ Монеты не найдены.")
            return

        text = (
            "📈 Сигнал на рост монеты:\n\n"
            f"Монета: {result['id'].upper()}\n"
            f"Цена входа: ${result['price']}\n"
            f"Цель +5%: ${round(result['price'] * 1.05, 4)}\n"
            f"Стоп-лосс: ${round(result['price'] * 0.955, 4)}\n"
            f"Изменение за 24ч: {result['change_24h']}%\n"
            f"Изменение за 7д: {result['change_7d']}%\n"
            f"Объём: ${result['volume']:,}"
        )
        await bot.send_message(USER_ID, text)
    except Exception as e:
        logging.error(f"Ошибка в send_signal(): {e}")
        await bot.send_message(USER_ID, f"⚠️ Ошибка при анализе монет:\n{e}")

# Команда /test
@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    await message.answer("✏️ Тестовый сигнал на основе анализа актуальных монет:")
    await send_signal()

# Кнопка «Получить ещё сигнал»
@dp.message_handler(lambda message: message.text.lower().startswith("🚀"))
async def more_signal(message: types.Message):
    await send_signal()

# Кнопка «Следить за монетой»
@dp.message_handler(lambda message: message.text.lower().startswith("🔔"))
async def watch_coin(message: types.Message):
    result = get_top_ton_wallet_coins()
    if result:
        coin = result['id']
        price = result['price']
        watchlist[coin] = {
            'start_price': price,
            'start_time': asyncio.get_event_loop().time(),
            'notified_3_5': False,
            'notified_5': False,
            'notified_timeout': False
        }
        await message.answer(f"⏱ Монета {coin.upper()} добавлена в отслеживание.")
    else:
        await message.answer("⚠️ Не удалось найти монету для отслеживания.")

# Проверка отслеживания каждые 10 минут
async def track_all():
    for coin, data in watchlist.items():
        try:
            await track_price_changes(bot, USER_ID, coin, data)
        except Exception as e:
            logging.error(f"Ошибка при отслеживании {coin}: {e}")

# Планировщик ежедневного сигнала
async def scheduled_signal():
    await send_signal()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    scheduler.add_job(scheduled_signal, 'cron', hour=8, minute=0)
    scheduler.add_job(track_all, 'interval', minutes=10)
    scheduler.start()

    executor.start_polling(dp, skip_updates=True)
