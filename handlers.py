from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from analysis import get_top_signal
from tracking import start_tracking, stop_all_trackings
from utils import reset_cache
from config import OWNER_ID

# Команда /start
async def start_command_handler(update: Update, context: CallbackContext):
    inline_keyboard = [
        [InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("🛑 Остановить все отслеживания", callback_data="stop_tracking")]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    reply_keyboard = [
        [KeyboardButton("Получить сигнал")],
        [KeyboardButton("Остановить все отслеживания")],
        [KeyboardButton("Сбросить кеш")]
    ]
    reply_markup_panel = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=reply_markup_inline
    )
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup_panel
    )

# Обработка inline-кнопок под сообщением
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

# Обработка reply-кнопок в панели
async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text.strip().lower()

    if "получить сигнал" in text:
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

    elif "остановить" in text:
        stop_all_trackings()
        await update.message.reply_text("⛔️ Отслеживание всех монет остановлено.")

    elif "сбросить кеш" in text:
        reset_cache()
        await update.message.reply_text("♻️ Кеш сброшен. Попробуй снова получить сигнал.")

# Объявление обработчиков
start_handler = CommandHandler("start", start_command_handler)
button_handler = CallbackQueryHandler(button_callback_handler)
