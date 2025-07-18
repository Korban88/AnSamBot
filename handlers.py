from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signals, clear_top_signals_cache

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")],
        [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_signals = await get_top_signals()
    if not top_signals:
        await update.effective_message.reply_text("Нет подходящих монет на текущий момент.")
        return

    # Упрощённая логика: возвращаем первую монету из топа
    coin = top_signals[0]
    keyboard = [
        [InlineKeyboardButton("Следить за монетой", callback_data=f"follow_{coin['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        f"Монета: {coin['name']}\n"
        f"Цена входа: {coin['entry_price']}\n"
        f"Цель: {coin['target_price']} (+5%)\n"
        f"Стоп-лосс: {coin['stop_loss']}\n"
        f"Текущая цена: {coin['price']}\n"
        f"Изменение за 24ч: {coin['change_24h']}%\n"
        f"Вероятность роста: {coin['growth_probability']}%"
    )

    await update.effective_message.reply_text(message_text, reply_markup=reply_markup)

async def follow_coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Функция отслеживания монеты временно недоступна.")

async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Функция остановки отслеживания временно недоступна.")

async def reset_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_top_signals_cache()
    await update.effective_message.reply_text("Кеш топ-сигналов сброшен.")
