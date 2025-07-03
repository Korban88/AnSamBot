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

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)

tracker = None

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("👁 Следить за монетой"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

def esc(text):
    if not isinstance(text, str):
        text = str(text)
    # Экранирование для MarkdownV2
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    for ch in escape_chars:
        text = text.replace(ch, '\\' + ch)
    return text

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован\\. Ждите сигналы каждый день в 8\\:00 МСК\\.")

@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_signals(message: types.Message):
    logging.info("Нажата кнопка 'Получить ещё сигнал'")
    await message.answer("⚙️ Обработка сигнала...")

    try:
        coins = get_top_coins()
        logging.info(f"COINS: {coins}")
        await message.answer(f"Найдено монет: {len(coins)}")

        if not coins:
            await message.answer("Не удалось получить сигналы\\. Попробуйте позже\\.")
            logging.warning("Список монет пуст, сигнал не отправлен.")
            return

        for coin in coins:
            try:
                name = esc(coin['id'])
                price = esc(coin['price'])
                change = esc(coin['change_24h'])
                probability = esc(coin['probability'])
                target_price = esc(coin['target_price'])
                stop_loss_price = esc(coin['stop_loss_price'])

                text = (
                    f"*💰 Сигнал:*\n"
                    f"Монета: *{name}*\n"
                    f"Цена: *{price} \\$*\n"
                    f"Рост за 24ч: *{change}\\%*\n"
                    f"{'🟢' if float(probability) >= 70 else '🔴'} Вероятность роста: *{probability}\\%*\n"
                    f"🎯 Цель: *{target_price} \\$* \\(\\+5\\%\\)\n"
                    f"⛔️ Стоп\\-лосс: *{stop_loss_price} \\$* \\(\\-3\\.5\\%\\)"
                )

                await message.answer(text)

            except Exception as e:
                safe_err = esc(str(e))
                await message.answer(f"⚠️ Ошибка: {safe_err}")

    except Exception as e:
        logging.error(f"Ошибка в get_top_coins: {e}")
        await message.answer(f"Произошла ошибка при получении сигналов: {esc(str(e))}")

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
            f"👁 Запущено отслеживание *{esc(coin_id)}*\nТекущая цена: *{esc(entry_price)} \\$*"
        )

    except Exception as e:
        safe_error = esc(str(e))
        await message.answer(f"❌ Ошибка запуска отслеживания: {safe_error}")

@dp.message_handler(Text(equals="🔴 Остановить все отслеживания"))
async def stop_tracking(message: types.Message):
    global tracker
    if tracker:
        tracker.stop_all_tracking()
        await message.answer("⛔️ Все отслеживания монет остановлены.")
    else:
        await message.answer("Нечего останавливать.")

async def on_startup(dispatcher):
    schedule_daily_signal(dispatcher, bot, get_top_coins, user_id=USER_ID)
    logging.info("Бот запущен и готов")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
