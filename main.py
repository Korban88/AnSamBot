import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from signal_generator import generate_signal
from tracker import CoinTracker

API_TOKEN = '8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c'
OWNER_ID = 347552741

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
tracker = CoinTracker(bot, 347552741)

# Главное меню без кнопки "Следить за монетой"
main_menu = InlineKeyboardMarkup(row_width=2)
main_menu.add(
    InlineKeyboardButton("🟢 Старт", callback_data='start'),
    InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data='more_signal'),
    InlineKeyboardButton("🔴 Остановить все отслеживания", callback_data='stop_all')
)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("<b>Бот активирован.</b> Ждите сигналы каждый день в 8:00 МСК.", reply_markup=main_menu)

@dp.callback_query_handler(lambda c: c.data == 'start')
async def process_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "<b>Бот активирован.</b> Ждите сигналы каждый день в 8:00 МСК.", reply_markup=main_menu)

@dp.callback_query_handler(lambda c: c.data == 'more_signal')
async def handle_more_signal(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    logger.info("Нажата кнопка 'Получить ещё сигнал'")
    signal = await generate_signal()

    if signal is None:
        await bot.send_message(callback_query.from_user.id, "⚠️ Нет подходящих монет для сигнала.")
        return

    text = signal['text']
    coin_id = signal['coin_id']
    track_button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👁 Следить за монетой", callback_data=f'track_{coin_id}')
    )
    await bot.send_message(callback_query.from_user.id, text, reply_markup=track_button)

@dp.callback_query_handler(lambda c: c.data.startswith('track_'))
async def handle_track(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    coin_id = callback_query.data.split('_', 1)[1]
    await tracker.add_coin(callback_query.from_user.id, coin_id)

@dp.callback_query_handler(lambda c: c.data == 'stop_all')
async def handle_stop_all(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await tracker.stop_all_tracking(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "❌ Все отслеживания остановлены.")

async def send_daily_signal():
    signal = await generate_signal()
    if signal:
        text = signal['text']
        coin_id = signal['coin_id']
        track_button = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👁 Следить за монетой", callback_data=f'track_{coin_id}')
        )
        await bot.send_message(OWNER_ID, text, reply_markup=track_button)
    else:
        await bot.send_message(OWNER_ID, "⚠️ Нет подходящих монет для сигнала.")

async def on_startup(dp):
    scheduler.add_job(send_daily_signal, trigger='cron', hour=8, minute=0, timezone='Europe/Moscow', id='send_signal')
    scheduler.start()
    await tracker.load_state()
    logger.info("⏳ До следующего сигнала: 1167.0 минут")

if __name__ == '__main__':
    from flask import Flask
    import threading

    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'Bot is running'

    def run_flask():
        app.run(host='0.0.0.0', port=8080)

    threading.Thread(target=run_flask).start()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
