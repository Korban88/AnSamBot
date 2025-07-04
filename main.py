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
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

tracker = None
signal_index = 0
cached_signals = []

# Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("👁 Следить за монетой"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

# Обработка команд

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")

@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_signals(message: types.Message):
    global signal_index, cached_signals
    logging.info("Нажата кнопка 'Получить ещё сигнал'")
    await message.answer("⚙️ Обработка сигнала...")

    try:
        if not cached_signals:
            cached_signals = get_top_coins()
            signal_index = 0

        if not cached_signals:
            await message.answer("Не удалось получить сигналы. Попробуйте позже.")
            return

        if signal_index >= len(cached_signals):
            await message.answer("Сигналы закончились. Попробуйте позже или нажмите 🟢 Старт для обновления.")
            return

        coin = cached_signals[signal_index]
        signal_index += 1

        name = coin['id']
        price = coin['price']
        change = coin['change_24h']
        probability = coin['probability']
        target_price = coin['target_price']
        stop_loss_price = coin['stop_loss_price']
        risky = coin.get('risky', False)

        risk_note = "\n⚠️ Монета имеет повышенный риск!" if risky else ""

        text = (
            f"💰 Сигнал:\n"
            f"Монета: {name}\n"
            f"Цена: {price} $\n"
            f"Рост за 24ч: {change}%\n"
            f"Вероятность роста: {probability}%\n"
            f"🎯 Цель: {target_price} $ (+5%)\n"
            f"⛔️ Стоп-лосс: {stop_loss_price} $ (-3.5%)"
            f"{risk_note}"
        )

        await message.answer(text)

    except Exception as e:
        logging.error(f"Ошибка при отправке сигнала: {e}")
        await message.answer(f"⚠️ Ошибка: {e}")

@dp.message_handler(Text(equals="👁 Следить за монетой"))
async def track_coin(message: types.Message):
    global tracker
    user_id = message.from_user.id

    if not cached_signals or signal_index == 0:
        await message.answer("Сначала получите сигнал, чтобы выбрать монету для отслеживания.")
        return

    # Отслеживать последнюю монету из сигналов
    coin = cached_signals[signal_index - 1]
    coin_id = coin['id']

    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()

    try:
        price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
        entry_price = float(price_data[coin_id]["usd"])

        tracker = CoinTracker(bot, user_id)
        tracker.start_tracking(coin_id, entry_price)
        tracker.run()

        await message.answer(
            f"👁 Запущено отслеживание {coin_id}\nТекущая цена: {entry_price} $"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка запуска отслеживания: {e}")

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
    logging.info("Бот запущен и готов.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
