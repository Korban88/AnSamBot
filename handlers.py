from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from tracking import start_tracking_coin, stop_all_trackings
from analysis import get_top_signals

OWNER_ID = 347552741

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Получить сигнал"], ["Остановить все отслеживания"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!\nВыберите действие:",
        reply_markup=reply_markup
    )

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_signals = await get_top_signals()
    if not top_signals:
        await update.message.reply_text("Нет подходящих монет сейчас.")
        return

    coin = top_signals[0]
    keyboard = [[InlineKeyboardButton("Следить за монетой", callback_data=f"follow_{coin['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"Монета: {coin['name']}\n"
        f"Вероятность роста: {coin['probability']}%\n"
        f"Цена входа: {coin['entry_price']}\n"
        f"Цель: {coin['target_price']}\n"
        f"Стоп-лосс: {coin['stop_loss']}"
    )
    await update.message.reply_text(message, reply_markup=reply_markup)

async def follow_coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    coin_id = query.data.replace("follow_", "")
    await start_tracking_coin(coin_id, query.from_user.id)

    await query.edit_message_text(f"Отслеживание монеты {coin_id} запущено.")

async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await stop_all_trackings(user_id)
    await update.message.reply_text("Все отслеживания остановлены.")
