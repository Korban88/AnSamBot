import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_utils import get_top_ton_wallet_coins

# Токен и ID
BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Глобальное хранилище монет для отслеживания
tracked_coin = None
tracked_price = None
tracked_start_time = None

# Функция для отправки сигнала
async def send_signal(message_obj):
    try:
        coin = get_top_ton_wallet_coins()
        name = coin['name']
        price = float(coin['price'])
        change_24h = float(coin['change_24h'])
        change_7d = float(coin['change_7d'])
        volume = coin['volume']

        target_price = price * 1.05
        stop_loss = price * 0.955
        probability = coin.get("probability", "~80%")

        signal_msg = (
            f"📈 Сигнал на рост монеты:\n"
            f"\n📅 Монета: {name}\n"
            f"📉 Цена входа: ${price:.4f}\n"
            f"🔢 Цель +5%: ${target_price:.4f}\n"
            f"⛔️ Стоп-лосс: ${stop_loss:.4f}\n"
            f"📊 Изменение за 24ч: {change_24h:.2f}%\n"
            f"📊 Изменение за 7д: {change_7d:.2f}%\n"
            f"💰 Объем: ${volume}\n"
            f"🔮 Вероятность роста: {probability}"
        )

        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🚀 Получить ещё сигнал", callback_data="get_signal"),
            InlineKeyboardButton("🔔 Следить за монетой", callback_data="track_signal")
        )

        await message_obj.answer(signal_msg, reply_markup=keyboard)
        return coin

    except Exception as e:
        logger.error(f"\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0430\u043d\u0430\u043b\u0438\u0437\u0435 \u043c\u043e\u043d\u0435\u0442: {e}")
        await message_obj.answer(f"⚠️ Ошибка при анализе монет: {e}")
        return None

# /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")

# /test
@dp.message_handler(commands=['test'])
async def cmd_test(message: types.Message):
    await send_signal(message)

# Обработка кнопок
@dp.callback_query_handler(lambda c: c.data == 'get_signal')
async def handle_get_signal(callback: types.CallbackQuery):
    await callback.answer()
    await send_signal(callback.message)

@dp.callback_query_handler(lambda c: c.data == 'track_signal')
async def handle_track(callback: types.CallbackQuery):
    global tracked_coin, tracked_price, tracked_start_time
    await callback.answer()
    tracked_coin = await send_signal(callback.message)
    if tracked_coin:
        tracked_price = float(tracked_coin['price'])
        tracked_start_time = asyncio.get_event_loop().time()
        logger.info(f"Started tracking {tracked_coin['name']} at price {tracked_price}")

# Ежедневно в 8:00 МСК
async def scheduled_signal():
    try:
        await bot.send_message(USER_ID, "\ud83c\udf1f Ежедневный сигнал")
        dummy = types.Message(message_id=1, chat=types.Chat(id=USER_ID, type='private'), date=None)
        await send_signal(dummy)
    except TelegramAPIError as e:
        logger.error(f"\u0421\u0431\u043e\u0439 \u043f\u0440\u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f: {e}")

scheduler.add_job(scheduled_signal, 'cron', hour=8, minute=0)

# Запуск
if __name__ == "__main__":
    scheduler.start()
    logger.info("\u0411\u043e\u0442 запущен и готов к работе.")
    executor.start_polling(dp, skip_updates=True)
