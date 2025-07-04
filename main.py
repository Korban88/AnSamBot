import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

from crypto_utils import get_top_coins
from tracking import CoinTracker
from scheduler import schedule_daily_signal
from keep_alive import keep_alive

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)

tracker = None
signal_index = 0
cached_signals = []

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

def esc(text):
    return str(text).replace('\\', '\\\\') \
        .replace('.', '\\.') \
        .replace('-', '\\-') \
        .replace('(', '\\(').replace(')', '\\)') \
        .replace('+', '\\+').replace('%', '\\%') \
        .replace('$', '\\$').replace('_', '\\_') \
        .replace('!', '\\!').replace(':', '\\:')

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован\\. Ждите сигналы каждый день в 8\\:00 МСК\\.")

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
            await message.answer("Не удалось получить сигналы\\. Попробуйте позже\\.")
            return

        if signal_index >= len(cached_signals):
            await message.answer("Сигналы закончились\\. Попробуйте позже или нажмите 🟢 Старт для обновления\\.")
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

        ma7 = coin["analysis"].get("ma7")
        ma20 = coin["analysis"].get("ma20")
        rsi_val = coin["analysis"].get("rsi")

        risk_note = "\n⚠️ *Монета имеет повышенный риск!*" if risky else ""

        text = (
            f"*💰 Сигнал:*\n"
            f"Монета: *{esc(name)}*\n"
            f"Цена: *{esc(price)} \\$*\n"
            f"Рост за 24ч: *{esc(change)}\\%*\n"
            f"RSI: *{esc(rsi_val)}*\n"
            f"MA7: *{esc(ma7)}*, MA20: *{esc(ma20)}*\n"
            f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: *{esc(probability)}\\%*\n"
            f"🎯 Цель: *{esc(target_price)} \\$* \\(\\+5\\%\\)\n"
            f"⛔️ Стоп\\-лосс: *{esc(stop_loss_price)} \\$* \\(\\-3\\.5\\%\\)"
            f"{risk_note}"
        )

        inline_btn = InlineKeyboardMarkup()
        inline_btn.add(InlineKeyboardButton(f"👁 Следить за {name}", callback_data=f"track_{name}"))

        await message.answer(text, reply_markup=inline_btn)

    except Exception as e:
        logging.error(f"Ошибка при отправке сигнала: {e}")
        safe_err = esc(str(e))
        await message.answer(f"⚠️ Ошибка: {safe_err}")

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def track_selected_coin(callback_query: types.CallbackQuery):
    global tracker
    coin_id = callback_query.data.replace("track_", "")
    logging.info(f"▶️ Получен callback: отслеживание {coin_id}")

    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()
    try:
        price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
        entry_price = float(price_data[coin_id]["usd"])

        tracker = CoinTracker(bot, callback_query.from_user.id)
        tracker.start_tracking(coin_id, entry_price)

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            f"👁 Отслеживание *{esc(coin_id)}* начато\\.\nТекущая цена: *{entry_price} \\$*",
            parse_mode="MarkdownV2"
        )

    except Exception as e:
        safe_error = esc(str(e))
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, f"❌ Ошибка запуска отслеживания: {safe_error}")

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
    keep_alive()
    logging.info("Бот запущен и готов.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
