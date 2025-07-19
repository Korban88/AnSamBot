import logging
import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder
from handlers import start_handler, button_callback_handler

from config import TELEGRAM_TOKEN, TELEGRAM_USER_ID
from utils import schedule_daily_signal_check

nest_asyncio.apply()  # ключевое для Replit / Railway

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Регистрируем обработчики
app.add_handler(start_handler)
app.add_handler(button_callback_handler)

# Планируем ежедневную задачу
async def run():
    schedule_daily_signal_check(app, TELEGRAM_USER_ID)
    await app.run_polling()

# Просто вызываем корутину напрямую без asyncio.run()
asyncio.get_event_loop().create_task(run())
