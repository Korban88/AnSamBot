from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signals
from tracking import stop_all_trackings
from config import OWNER_ID

user_signal_index = {}

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Получить сигнал", callback_data="get_signal")],
        [InlineKeyboardButton("Остановить все отслеживания", callback_data="stop_tracking")],
        [InlineKeyboardButton("Сбросить кеш", callback_data="reset_cache")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_main_keyboard()
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=keyboard)

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_signal_index:
        user_signal_index[chat_id] = 0

    top_signals = await get_top_signals()
    signal_index = user_signal_index[chat_id] % len(top_signals)
    signal = top_signals[signal_index]
    user_signal_index[chat_id] += 1

    message = (
        f"Монета: {signal['name']}\n"
        f"Цена входа: {signal['entry_price']}\n"
        f"Цель: {signal['target_price']} (+5%)\n"
        f"Стоп-лосс: {signal['stop_loss']}\n"
        f"Текущая цена: {signal['entry_price']}\n"
        f"Изменение за 24ч: {round((signal['target_price'] - signal['entry_price']) / signal['entry_price'] * 100, 2)}%\n"
        f"Вероятность роста: {signal['probability']}%\n"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Следить за монетой", callback_data=f"follow_{signal['id']}")]
    ])

    await update.message.reply_text(message, reply_markup=keyboard)

async def follow_coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Отслеживание запущено!")

async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_all_trackings()
    await update.message.reply_text("Все отслеживания остановлены.")

async def reset_cache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        from crypto_utils import reset_top_signals_cache
        reset_top_signals_cache()
        await update.message.reply_text("Кеш сигналов сброшен.")
    else:
        await update.message.reply_text("У вас нет прав для этой команды.")
