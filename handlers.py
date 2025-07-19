from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
from utils import reset_cache  # <-- импорт из utils.py

USER_ID = 347552741

main_menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
])

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=main_menu_keyboard)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        result = await get_top_signal()
        if result:
            await query.message.reply_text(result["text"], reply_markup=result["markup"], parse_mode="MarkdownV2")
        else:
            await query.message.reply_text("Нет подходящих монет для сигнала.")

    elif query.data == "stop_tracking":
        await stop_all_trackings()
        await query.message.reply_text("Все отслеживания остановлены.")

    elif query.data == "reset_cache":
        message = reset_cache()
        await query.message.reply_text(message)
