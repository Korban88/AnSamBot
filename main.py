import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

from crypto_utils import get_top_coins
from tracking import CoinTracker
from scheduler import schedule_daily_signal

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)

# Отключаем Markdown
bot = Bot(token=BOT_TOKEN, parse_mode=None)
dp = Dispatcher(bot)

tracker = None

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("👁 Следить за монетой"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")

@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_signals(message: types.Message):
    logging.info("Нажата кнопка 'Получить ещё сигнал'")
    await message.answer("⚙️ Обработка сигнала...")

    try:
        coins = get_top_coins()
        logging.info(f"COINS: {coins}")

        if not coins:
            await message.answer("Не удалось получить сигналы. Попробуйте позже.")
            logging.warning("Список монет пуст, сигнал не отправлен.")
            return

        for coin in coins:
            try:
                text = (
                    f"Сигнал:\n"
                    f"Монета: {coin['id']}\n"
                    f"Цена: {coin['price']} $\n"
                    f"Рост за 24ч: {coin['change_24h']}%\n"
                    f"Вероятность роста: {coin['probability']}%\n"
                    f"Цель: {coin['target_price']} $\n"
                    f"Стоп-лосс: {coin['stop_loss_price']} $"
                )
                await message.answer(text)
                logging.info(f"Отправлен сигнал по монете: {coin['id']}")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения по монете {coin['id']}: {e}")
                await message.answer(f"⚠️ Ошибка: {e}")
    except Exception as e:
        logging.error(f"Ошибка в get_top_coins: {e}")
        await message.answer(f"Произошла ошибка при получении сигналов: {e}")

@dp.message_handler(Text(equals="👁 Следить за монетой"))
async def track_coin(message: types.Message):
    global tracker
    user_id = message.from_user.id
    coin_id = "toncoin"

    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()
    try:
        price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
        entry_price = float(price_data[coin_id]["usd"])

        tracker = CoinTracker(bot, user_id)
        tracker.start_tracking(coin_id, entry_price)
        tracker.run()

        await message.answer(
            f"Запущено отслеживание {coin_id}\nТекущая цена: {entry_price} $"
        )

    except Exception as e:
        logging.error(f"Ошибка запуска отслеживания: {e}")
        await message.answer(f"❌ Ошибка запуска отслеживания: {e}")

@dp.message_handler(Text(equals="🔴 Остановить все отслеживания"))
async def stop_tracking(message: types.Message):
    global tracker
    if tracker:
        tracker.stop_all_tracking()
        await message.answer("Все отслеживания монет остановлены.")
    else:
        await message.answer("Нечего останавливать.")

async def on_startup(dispatcher):
    schedule_daily_signal(dispatcher, bot, get_top_coins, user_id=USER_ID)
    logging.info("Бот запущен и готов")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
