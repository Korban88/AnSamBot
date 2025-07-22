import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from config import OWNER_ID
from analysis import get_top_signal
from tracking import start_tracking

def reset_cache():
    """
    Сброс кэша использованных монет
    """
    used_path = "used_symbols.json"
    if os.path.exists(used_path):
        os.remove(used_path)

async def send_signal_message(app):
    """
    Отправка сигнала владельцу: лучшая монета на текущий момент
    """
    signal = get_top_signal()
    if not signal:
        await app.bot.send_message(chat_id=OWNER_ID, text="🚫 Нет подходящих монет для сигнала.")
        return

    symbol = signal.get("symbol", "").upper()
    name = signal.get("name", "")
    current_price = signal.get("current_price", 0)
    target_price = round(current_price * 1.05, 4)
    stop_loss = round(current_price * 0.965, 4)
    change_24h = round(signal.get("price_change_percentage_24h", 0), 2)
    probability = signal.get("probability", 0)

    message = f"*💹 Сигнал на рост: {symbol} ({name})*\n\n" \
              f"Текущая цена: `${current_price}`\n" \
              f"🎯 Цель: +5% → `${target_price}`\n" \
              f"🛡 Стоп-лосс: `${stop_loss}`\n" \
              f"📈 Изменение за 24ч: `{change_24h}%`\n" \
              f"📊 Вероятность роста: *{probability}%*\n"

    # Кнопка "Следить"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{symbol}")]
    ])

    await app.bot.send_message(
        chat_id=OWNER_ID,
        text=message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def schedule_daily_signal_check(app):
    """
    Запускает планировщик отправки сигнала каждый день в 8:00 по МСК
    """
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(lambda: app.create_task(send_signal_message(app)),
                      trigger='cron', hour=8, minute=0, id='daily_signal')
    scheduler.start()
