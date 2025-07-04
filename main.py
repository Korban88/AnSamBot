import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import filters
from aiogram.types import CallbackQuery

from crypto_utils import get_top_coins
from tracking import CoinTracker
from scheduler import schedule_daily_signal

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

tracker = None
signal_index = 0
cached_signals = []

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

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

        risk_note = "\n⚠️ <b>Монета имеет повышенный риск!</b>" if risky else ""

        text = (
            f"<b>💰 Сигнал:</b>\n"
            f"Монета: <b>{name}</b>\n"
            f"Цена: <b>{price} $</b>\n"
            f"Рост за 24ч: <b>{change}%</b>\n"
            f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: <b>{probability}%</b>\n"
            f"🎯 Цель: <b>{target_price} $</b> (+5%)\n"
            f"⛔️ Стоп-лосс: <b>{stop_loss_price} $</b> (-3.5%)"
            f"{risk_note}"
        )

        # 🔘 Инлайн-кнопка
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track:{name}:{price}"))

        await message.answer(text, reply_markup=inline_kb)

    except Exception as e:
        logging.error(f"Ошибка при отправке сигнала: {e}")
        await message.answer(f"⚠️ Ошибка: {str(e)}")

@dp.callback_query_handler(lambda c: c.data.startswith("track:"))
async def process_tracking_callback(callback_query: CallbackQuery):
    global tracker
    _, coin_id, entry_price = callback_query.data.split(":")
    entry_price = float(entry_price)

    tracker = CoinTracker(bot, callback_query.from_user.id)
    tracker.start_tracking(coin_id, entry_price)
    tracker.run()

    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        f"👁 Запущено отслеживание <b>{coin_id}</b>\nТекущая цена: <b>{entry_price} $</b>"
    )

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
