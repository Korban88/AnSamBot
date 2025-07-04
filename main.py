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

# Главное меню
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("📈 Получить ещё сигнал")

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if message.chat.id != USER_ID:
        return
    await message.answer("✅ Бот запущен и готов находить сигналы.", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "📈 Получить ещё сигнал")
async def handle_signal(message: types.Message):
    if message.chat.id != USER_ID:
        return

    result = generate_signal()
    if not result:
        await message.answer("⚠️ Сейчас нет подходящих монет. Но рынок живёт — запроси ещё чуть позже.")
        return

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

    buttons = types.InlineKeyboardMarkup()
    buttons.add(types.InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await message.answer(text, reply_markup=buttons)

@dp.callback_query_handler(lambda call: call.data.startswith("track_"))
async def handle_track(call: types.CallbackQuery):
    coin = call.data.split("_")[1]
    await tracker.track_coin(coin)
    await call.answer(f"🟢 Отслеживаю {coin} на +3.5% и +5%")

async def send_daily_signal():
    result = generate_signal()
    if not result:
        await bot.send_message(USER_ID, "⚠️ Сегодня нет подходящих монет.")
        return

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

    buttons = types.InlineKeyboardMarkup()
    buttons.add(types.InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{result['symbol']}"))

    await bot.send_message(USER_ID, text, reply_markup=buttons)

async def on_startup(dp):
    scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0)
    scheduler.start()
    print("✅ Бот готов к работе.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
