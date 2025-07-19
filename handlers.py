from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signals
from tracking import stop_all_tracking, track_coin_price
from crypto_utils import reset_top_signals_cache

# Главные кнопки
main_keyboard = [
    [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
    [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")],
    [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")]
]
main_markup = InlineKeyboardMarkup(main_keyboard)

# Формат сигнала
def format_signal(signal):
    return (
        f"*Монета:* {signal['name']}\n"
        f"*Цена входа:* {signal['entry_price']}\n"
        f"*Цель:* {signal['target_price']} (+5%)\n"
        f"*Стоп-лосс:* {signal['stop_loss']}\n"
        f"*Текущая цена:* {signal['entry_price']}\n"
        f"*Изменение за 24 часа:* {signal['change_24h']}%\n"
        f"*Вероятность роста:* {signal['probability']}%"
    )

# Обработка команды /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=main_markup
    )

# Обработка текстовых сообщений (альтернатива кнопкам)
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "сброс" in text:
        await reset_cache_handler(update, context)
    elif "останов" in text:
        await stop_tracking_handler(update, context)
    elif "сигнал" in text:
        await get_signal_handler(update, context)
    else:
        await update.message.reply_text("Выберите действие:", reply_markup=main_markup)

# Обработка кнопок
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        await get_signal_handler(update, context, query=query)
    elif query.data == "reset_cache":
        await reset_cache_handler(update, context, query=query)
    elif query.data == "stop_tracking":
        await stop_tracking_handler(update, context, query=query)
    elif query.data.startswith("track_"):
        coin_id = query.data.replace("track_", "")
        await track_coin_price(update, context, coin_id, query=query)

# Получить сигнал
async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    signals = await get_top_signals()
    if not signals:
        message = "Нет подходящих монет для сигнала."
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    signal = signals.pop(0)
    signals.append(signal)  # ротация
    context.bot_data["cached_signals"] = signals

    text = format_signal(signal)
    track_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Следить за монетой", callback_data=f"track_{signal['id']}")]
    ])
    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=track_button)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=track_button)

# Сбросить кеш
async def reset_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    reset_top_signals_cache()
    context.bot_data["cached_signals"] = []
    text = "Кеш сигналов сброшен."
    if query:
        await query.edit_message_text(text, reply_markup=main_markup)
    else:
        await update.message.reply_text(text, reply_markup=main_markup)

# Остановить все отслеживания
async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    stop_all_tracking()
    text = "Все отслеживания остановлены."
    if query:
        await query.edit_message_text(text, reply_markup=main_markup)
    else:
        await update.message.reply_text(text, reply_markup=main_markup)
