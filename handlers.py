from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
from utils import reset_cache

keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
])

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=keyboard
    )

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        signal = await get_top_signal()
        if signal:
            text = (
                f"💹 *Сигнал на покупку:*\n\n"
                f"*Монета:* `{signal['symbol']}`\n"
                f"*Цена входа:* {signal['entry_price']}\n"
                f"*Цель:* +5% → {signal['target_price']}\n"
                f"*Стоп-лосс:* {signal['stop_loss']}\n"
                f"*Изменение за 24ч:* {signal['change_24h']}%\n"
                f"*Вероятность роста:* {signal['probability']}%\n"
                f"\n_Анализ проведён по ключевым метрикам рынка._"
            )
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['symbol']}")]
            ])
            await query.message.reply_text(text, reply_markup=button, parse_mode="MarkdownV2")
        else:
            await query.message.reply_text("Сейчас нет подходящих монет по стратегии.")

    elif query.data == "reset_cache":
        reset_cache()
        await query.message.reply_text("🔄 Кеш успешно сброшен.")

    elif query.data == "stop_tracking":
        stop_all_trackings()
        await query.message.reply_text("🚫 Все отслеживания остановлены.")

    elif query.data.startswith("track_"):
        symbol = query.data.replace("track_", "")
        await start_tracking(symbol, context)
        await query.message.reply_text(f"⏱ Отслеживаю {symbol} каждые 10 минут.")
