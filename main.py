import logging
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from signal_generator import generate_signal
from config import BOT_TOKEN, USER_ID
from coin_tracker import CoinTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot, USER_ID)

user_state = {}

keyboard_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_main.add("📈 Получить ещё сигнал")

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if message.chat.id != USER_ID:
        return
    await message.answer("Бот запущен. Я готов находить для тебя лучшие монеты.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True))
    await message.answer("Выбери действие:", reply_markup=keyboard_main)

@dp.message_handler(lambda message: message.text == "📈 Получить ещё сигнал")
async def send_signal(message: types.Message):
    if message.chat.id != USER_ID:
        return

    result = generate_signal()
    logger.info("🔍 Получен результат сигнала: %s", result)

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"🔹 Символ: `{result['symbol']}`\n"
        f"💰 Цена входа: *{result['entry']} USD*\n"
        f"🎯 Цель (+5%): *{result['target']} USD*\n"
        f"🛡️ Стоп-лосс: *{result['stop']} USD*\n\n"
        f"📊 Изменение за 24ч: *{result['change_24h']}%*\n"
        f"📈 RSI: *{result['rsi']}*\n"
        f"📉 MA7: *{result['ma7']}*, MA20: *{result['ma20']}*\n"
        f"🧠 Оценка (score): *{result['score']}*\n"
        f"📈 Вероятность роста: *{result['probability']}%*"
    )

    inline_btn = types.InlineKeyboardMarkup()
    inline_btn.add(types.InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await message.answer(text, reply_markup=inline_btn)

@dp.callback_query_handler(lambda call: call.data.startswith("track_"))
async def track_coin(call: types.CallbackQuery):
    coin_symbol = call.data.split("_")[1]
    await tracker.track_coin(coin_symbol)
    await call.answer(f"Теперь отслеживаю {coin_symbol} на +3.5% и +5%")

async def send_daily_signal():
    result = generate_signal()
    logger.info("📤 Ежедневный сигнал: %s", result)

    text = (
        f"💡 *Сигнал на рост: {result['name']}*\n\n"
        f"🔹 Символ: `{result['symbol']}`\n"
        f"💰 Цена входа: *{result['entry']} USD*\n"
        f"🎯 Цель (+5%): *{result['target']} USD*\n"
        f"🛡️ Стоп-лосс: *{result['stop']} USD*\n\n"
        f"📊 Изменение за 24ч: *{result['change_24h']}%*\n"
        f"📈 RSI: *{result['rsi']}*\n"
        f"📉 MA7: *{result['ma7']}*, MA20: *{result['ma20']}*\n"
        f"🧠 Оценка (score): *{result['score']}*\n"
        f"📈 Вероятность роста: *{result['probability']}%*"
    )

    inline_btn = types.InlineKeyboardMarkup()
    inline_btn.add(types.InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await bot.send_message(USER_ID, text, reply_markup=inline_btn)

async def on_startup(dp):
    scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
    scheduler.start()
    logger.info("✅ Бот готов к работе.")
    print("⏳ До следующего сигнала: 1167.0 минут")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
