from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from analysis import get_top_signal
from config import OWNER_ID

scheduler = AsyncIOScheduler()

def schedule_daily_signal_check(app):
    scheduler.add_job(send_daily_signal, "cron", hour=8, minute=0, args=[app])
    scheduler.start()

async def send_daily_signal(app):
    signal = await get_top_signal()
    if signal:
        text = (
            f"📈 *Сигнал дня*\n"
            f"Монета: *{signal['symbol']}*\n"
            f"Цена входа: *{signal['entry_price']}*\n"
            f"Цель: *{signal['target_price']}* (+5%)\n"
            f"Стоп-лосс: *{signal['stop_loss']}*\n"
            f"Изменение за 24ч: *{signal['change_24h']}%*\n"
            f"Вероятность роста: *{signal['probability']}%*"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
        ])

        await app.bot.send_message(
            chat_id=OWNER_ID,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    else:
        await app.bot.send_message(
            chat_id=OWNER_ID,
            text="Сегодня нет подходящих сигналов.",
        )

def reset_cache():
    from os import remove
    try:
        remove("used_symbols.json")
    except FileNotFoundError:
        pass
