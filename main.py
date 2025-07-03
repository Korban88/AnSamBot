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

def esc_md(text: str) -> str:
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

        if not coins:
            await message.answer("Не удалось получить сигналы\\. Попробуйте позже\\.")
            logging.warning("Список монет пуст, сигнал не отправлен.")
            return

        for coin in coins:
            text_md = (
                f"*💰 Сигнал:*\n"
                f"Монета: *{esc_md(str(coin['id']))}*\n"
                f"Цена: *{esc_md(str(coin['price']))} \\$*\n"
                f"Рост за 24ч: *{esc_md(str(coin['change_24h']))}\\%*\n"
                f"{'🟢' if float(coin['probability']) >= 70 else '🔴'} Вероятность роста: *{esc_md(str(coin['probability']))}\\%*\n"
                f"🎯 Цель: *{esc_md(str(coin['target_price']))} \\$* \\(\\+5\\%\\)\n"
                f"⛔️ Стоп\\-лосс: *{esc_md(str(coin['stop_loss_price']))} \\$* \\(\\-3\\.5\\%\\)"
            )
            text_plain = (
                f"Сигнал:\n"
                f"Монета: {coin['id']}\n"
                f"Цена: {coin['price']} $\n"
                f"Рост за 24ч: {coin['change_24h']}%\n"
                f"Вероятность роста: {coin['probability']}%\n"
                f"Цель: {coin['target_price']} $\n"
                f"Стоп-лосс: {coin['stop_loss_price']} $"
            )
            try:
                await message.answer(text_md, parse_mode="MarkdownV2")
                logging.info(f"Отправлен сигнал по монете: {coin['id']} с MarkdownV2")
            except Exception as e:
                logging.error(f"Ошибка MarkdownV2 при отправке {coin['id']}: {e}. Отправляю без форматирования.")
                try:
                    await message.answer(text_plain, parse_mode=None)
                except Exception as ex:
                    logging.error(f"Ошибка при отправке без форматирования {coin['id']}: {ex}")
                    await message.answer(f"⚠️ Ошибка при отправке сигнала по монете {coin['id']}")

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
            f"👁 Запущено отслеживание *{esc_md(coin_id)}*\nТекущая цена: *{esc_md(str(entry_price))} \\$*"
        )

    except Exception as e:
        logging.error(f"Ошибка запуска отслеживания: {e}")
        await message.answer(f"❌ Ошибка запуска отслеживания: {esc_md(str(e))}")

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
