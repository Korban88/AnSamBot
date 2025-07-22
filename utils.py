import json
import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from analysis import get_top_signal

scheduler = AsyncIOScheduler()

def schedule_daily_signal_check(app, user_id):
    scheduler.add_job(
        lambda: send_signal(app, user_id),
        CronTrigger(hour=8, minute=0, timezone="Europe/Moscow"),
        id="daily_signal",
        replace_existing=True,
    )
    scheduler.start()

async def send_signal(app, user_id):
    try:
        signal = await get_top_signal()
        if not signal:
            await app.bot.send_message(chat_id=user_id, text="Сегодня нет надёжных сигналов.")
            return

        text = (
            f"*💹 Сигнал на покупку монеты: {signal['symbol']}*\n"
            f"Цена входа: `{signal['entry_price']}` $\n"
            f"Цель: `{signal['target_price']}` (+5%)\n"
            f"Стоп-лосс: `{signal['stop_loss']}`\n"
            f"Изменение за 24ч: `{signal['change_24h']}%`\n"
            f"Вероятность роста: *{signal['probability']}%*"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
        ])

        await app.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.exception("Ошибка при отправке сигнала")
        await app.bot.send_message(chat_id=user_id, text=f"Ошибка при отправке сигнала: {e}")

def reset_cache():
    for file in ["used_symbols.json", "signals_cache.json", "indicators_cache.json"]:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
