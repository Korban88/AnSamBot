from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings

def get_reply_keyboard():
    return ReplyKeyboardMarkup([
        ["📈 Получить сигнал"],
        ["🛑 Остановить все отслеживания"],
        ["♻️ Сбросить кеш"]
    ], resize_keyboard=True)

async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=get_reply_keyboard()
    )

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        signal = await get_top_signal()

        if signal:
            message = (
                f"Монета: *{signal['symbol']}*\n"
                f"Цена входа: *{signal['entry_price']}* $\n"
                f"Цель +5%: *{signal['target_price']}* $\n"
                f"Стоп-лосс: *{signal['stop_loss']}* $\n"
                f"Изменение за 24ч: *{signal['change_24h']}%*\n"
                f"Вероятность роста: *{signal['probability']}%*"
            )
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
            ])
            await query.message.reply_text(message, reply_markup=button, parse_mode="Markdown")
        else:
            await query.message.reply_text("Нет подходящих сигналов. Попробуй позже.")

    elif query.data == "stop_tracking":
        stop_all_trackings()
        await query.message.reply_text("⛔️ Отслеживание всех монет остановлено.")

    elif query.data.startswith("track_"):
        symbol = query.data.replace("track_", "")
        start_tracking(symbol)
        await query.message.reply_text(f"🔔 Теперь отслеживаем монету *{symbol}*", parse_mode="Markdown")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "сигнал" in text.lower():
        signal = await get_top_signal()
        if signal:
            message = (
                f"Монета: *{signal['symbol']}*\n"
                f"Цена входа: *{signal['entry_price']}* $\n"
                f"Цель +5%: *{signal['target_price']}* $\n"
                f"Стоп-лосс: *{signal['stop_loss']}* $\n"
                f"Изменение за 24ч: *{signal['change_24h']}%*\n"
                f"Вероятность роста: *{signal['probability']}%*"
            )
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Следить за монетой", callback_data=f"track_{signal['symbol']}")]
            ])
            await update.message.reply_text(message, reply_markup=button, parse_mode="Markdown")
        else:
            await update.message.reply_text("Нет подходящих сигналов. Попробуй позже.")

    elif "остановить" in text.lower():
        stop_all_trackings()
        await update.message.reply_text("⛔️ Все отслеживания остановлены.")

    elif "сброс" in text.lower():
        from crypto_utils import reset_cache
        reset_cache()
        await update.message.reply_text("♻️ Кеш очищен.")
