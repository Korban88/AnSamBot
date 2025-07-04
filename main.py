import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

from crypto_utils import get_top_coins
from scheduler import schedule_daily_signal

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# Храним индекс текущей монеты, чтобы при нажатии на кнопку показывать следующую
user_coin_index = {}

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("🟢 Старт"),
    KeyboardButton("🚀 Получить ещё сигнал")
)
keyboard.add(
    KeyboardButton("👁 Следить за монетой"),
    KeyboardButton("🔴 Остановить все отслеживания")
)


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)


@dp.message_handler(Text(equals="🟢 Старт"))
async def activate_bot(message: types.Message):
    await message.answer("Бот активирован. Ждите сигналы каждый день в 8:00 МСК.")


@dp.message_handler(Text(equals="🚀 Получить ещё сигнал"))
async def send_next_coin(message: types.Message):
    user_id = message.from_user.id
    logging.info("Нажата кнопка 'Получить ещё сигнал'")

    coins = get_top_coins()
    if not coins:
        await message.answer("❌ Не удалось получить сигналы. Попробуйте позже.")
        return

    if user_id not in user_coin_index:
        user_coin_index[user_id] = 0
    index = user_coin_index[user_id]

    if index >= len(coins):
        await message.answer("⚠️ Сигналы на сегодня закончились. Попробуйте позже.")
        return

    coin = coins[index]
    user_coin_index[user_id] += 1

    text = (
        f"💰 *Сигнал:*\n"
        f"Монета: *{coin['id']}*\n"
        f"Цена: *{coin['price']} $*\n"
        f"Рост за 24ч: *{coin['change_24h']}%*\n"
        f"{'🟢' if coin['probability'] >= 70 else '🔴'} Вероятность роста: *{coin['probability']}%*\n"
        f"🎯 Цель: *{coin['target_price']} $* (+5%)\n"
        f"⛔️ Стоп-лосс: *{coin['stop_loss_price']} $* (-3.5%)"
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message_handler(Text(equals="👁 Следить за монетой"))
async def track_coin(message: types.Message):
    await message.answer("⚙️ Функция отслеживания монет будет активирована позже.")


@dp.message_handler(Text(equals="🔴 Остановить все отслеживания"))
async def stop_tracking(message: types.Message):
    await message.answer("⛔️ Все отслеживания монет остановлены.")


async def on_startup(dispatcher):
    logging.info("Бот запущен и готов.")
    schedule_daily_signal(dispatcher, bot, get_top_coins, user_id=USER_ID)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
