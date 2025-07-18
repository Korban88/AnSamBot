from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.signals import get_top_signals
from tracking import start_tracking, stop_all_trackings
import os

# Старт
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")],
        [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

# Получить сигнал
signal_index = {}

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    top_signals = await get_top_signals()

    index = signal_index.get(user_id, 0)
    signal = top_signals[index % len(top_signals)]
    signal_index[user_id] = index + 1

    text = (
        f"*Монета:* {signal['name']}\n"
        f"*Цена входа:* {signal['entry_price']}\n"
        f"*Цель:* {signal['target_price']} (+5%)\n"
        f"*Стоп-лосс:* {signal['stop_loss']}\n"
        f"*Вероятность роста:* {signal['probability']}%"
    )
    keyboard = [
        [InlineKeyboardButton("Следить за монетой", callback_data=f"follow_{signal['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# Следить за монетой
async def follow_coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    coin_id = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    await start_tracking(user_id, coin_id, context)

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(f"⏱ Монета *{coin_id}* теперь под наблюдением!", parse_mode="Markdown")

# Остановить отслеживание
async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stop_all_trackings(user_id)
    await update.message.reply_text("❌ Все отслеживания остановлены.")

# Сброс кеша
async def reset_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists("top_signals_cache.json"):
        os.remove("top_signals_cache.json")
        await update.message.reply_text("🧹 Кеш очищен.")
    else:
        await update.message.reply_text("Кеш уже пуст.")
