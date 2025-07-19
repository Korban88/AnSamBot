from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
from config import OWNER_ID

def start_command_handler(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup
    )

async def button_callback_handler(update: Update, context: CallbackContext):
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

# Объявляем обработчики, которые можно импортировать в main.py
start_handler = CommandHandler("start", start_command_handler)
button_handler = CallbackQueryHandler(button_callback_handler)
