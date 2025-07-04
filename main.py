import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from crypto_utils import get_top_coins
from scheduler import schedule_daily_signal
from tracking import CoinTracker

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)

tracker = None
sent_coin_ids = []

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("🟢 Старт"))
keyboard.add(KeyboardButton("🚀 Получить ещё сигнал"))
keyboard.add(KeyboardButton("🔴 Остановить все отслеживания"))

def esc(text):
    return str(text).replace("-", "\\-").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("+", "\\+").replace("%", "\\%").replace("$", "\\$").replace("_", "\\_")

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован\\. Ждите сигналы каждый день в 8\\:00 МСК\\.")

@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_next_signal(message: types.Message):
    global sent_coin_ids
    await message.answer("⚙️ Обработка сигнала...")

    coins = get_top_coins()
    filtered = [coin for coin in coins if coin["id"] not in sent_coin_ids]

    if not filtered:
        sent_coin_ids = []
        filtered = coins

    coin = filtered[0]
    sent_coin_ids.append(coin["id"])

    name = coin['id']
    price = coin['price']
    change = coin['change_24h']
    probability = coin['probability']
    target_price = coin['target_price']
    stop_loss_price = coin['stop_loss_price']

    text = (
        f"💰 *Сигнал:*\n"
        f"Монета: *{esc(name)}*\n"
        f"Цена: *{esc(price)} \\$*\n"
        f"Рост за 24ч: *{esc(change)}\\%*\n"
        f"{'🟢' if probability >= 70 else '🔴'} Вероятность роста: *{esc(probability)}\\%*\n"
        f"🎯 Цель: *{esc(target_price)} \\$* \\(\\+5\\%\\)\n"
        f"⛔️ Стоп\\-лосс: *{esc(stop_loss_price)} \\$* \\(\\-3\\.5\\%\\)"
    )

    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton(text="👁 Следить за монетой", callback_data=f"track_{name}_{price}"))

    await message.answer(text, reply_markup=inline_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("track_"))
async def process_tracking(callback_query: types.CallbackQuery):
    global tracker
    _, coin_id, price_str = callback_query.data.split("_")
    entry_price = float(price_str)

    tracker = CoinTracker(bot, callback_query.from_user.id)
    tracker.start_tracking(coin_id, entry_price)
    tracker.run()

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"👁 Запущено отслеживание *{coin_id}*\nТекущая цена: *{entry_price} \\$*"
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
    logging.info("Бот запущен и готов")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
