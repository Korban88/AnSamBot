import logging
import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder
from handlers import start_handler, button_callback_handler
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID
from utils import schedule_daily_signal_check

nest_asyncio.apply()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Регистрируем обработчики
app.add_handler(start_handler)
app.add_handler(button_callback_handler)

# Планируем ежедневную задачу
async def run():
    schedule_daily_signal_check(app, TELEGRAM_USER_ID)
    await app.run_polling()

# Запускаем бота через уже существующий event loop
loop = asyncio.get_event_loop()
loop.create_task(run())
loop.run_forever()
