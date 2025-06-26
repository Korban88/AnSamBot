import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import datetime

# === НАСТРОЙКИ ===
API_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741  # Только для Артура

# === БАЗА ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# === КНОПКА "Сообщить об ошибке" ===
def get_error_button():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📩 Сообщить об ошибке", callback_data="report_issue"))
    return kb

# === ОБРАБОТКА СТАРТА ===
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    if message.from_user.id == USER_ID:
        await message.answer(
            "Добро пожаловать в новую жизнь, Корбан!\nAnSam Bot подключён. Первый сигнал придёт в 12:00 по Москве.",
            reply_markup=get_error_button()
        )
    else:
        await message.answer("У вас нет доступа к этому боту.")

# === ОБРАБОТКА КНОПКИ "Сообщить об ошибке" ===
@dp.callback_query_handler(lambda c: c.data == "report_issue")
async def process_callback_report(callback_query: types.CallbackQuery):
    await bot.send_message(USER_ID, "🚨 Принято. Ты сообщил об ошибке. Я всё проверю.")
    await bot.answer_callback_query(callback_query.id)

# === ОТПРАВКА СИГНАЛА ===
async def daily_signal():
    today = datetime.date.today()
    await bot.send_message(USER_ID,
        f"🎯 Сигнал от AnSam Bot на {today}:\n"
        f"Монета: TON\n"
        f"Вход: $6.00\n"
        f"Цель: $6.30 (+5%)\n"
        f"Стоп: $5.80",
        reply_markup=get_error_button()
    )

# === ПЛАНИРОВЩИК ===
async def scheduler():
    while True:
        now = datetime.datetime.now()
        if now.hour == 12 and now.minute == 0:
            await daily_signal()
            await asyncio.sleep(60)
        await asyncio.sleep(20)

# === ЗАПУСК ===
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, skip_updates=True)
