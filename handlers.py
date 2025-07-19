from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
from utils import reset_cache

keyboard = [
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
]
markup = InlineKeyboardMarkup(keyboard)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=markup)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        signal = await get_top_signal()
        if signal:
            text = (
                f"*Монета:* {signal['symbol']}\n"
                f"*Цена входа:* {signal['entry_price']}\n"
                f"*Цель:* {signal['target_price']} (+5%)\n"
                f"*Стоп-лосс:* {signal['stop_loss']}\n"
                f"*Текущая цена:* {signal['current_price']}\n"
                f"*Изменение за 24 часа:* {signal['change_24h']}%\n"
                f"*Вероятность роста:* {signal['probability']}%"
            )
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['symbol']}")]
            ])
            await query.message.reply_text(text, reply_markup=button, parse_mode="Markdown")
        else:
            await query.message.reply_text("Нет подходящих монет для сигнала.")
    elif query.data == "reset_cache":
        reset_cache()
        await query.message.reply_text("Кеш очищен.")
    elif query.data == "stop_tracking":
        stop_all_trackings()
        await query.message.reply_text("Все отслеживания остановлены.")
    elif query.data.startswith("track_"):
        symbol = query.data.split("_")[1]
        await start_tracking(symbol, query.message.chat_id, context)
        await query.message.reply_text(f"Монета {symbol} будет отслеживаться.")
