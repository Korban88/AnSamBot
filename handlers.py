from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from analysis import get_top_signals

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Получить сигнал"],
        ["Остановить все отслеживания"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в новую жизнь, Корбан!", reply_markup=reply_markup)

    # Сбрасываем счётчик сигнала при новом старте
    context.chat_data['signal_index'] = 0

async def get_signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_signals = await get_top_signals()
    if not top_signals:
        await update.message.reply_text("Нет подходящих монет на текущий момент.")
        return

    # Получаем текущий индекс, если нет — начинаем с 0
    signal_index = context.chat_data.get('signal_index', 0) % len(top_signals)
    coin = top_signals[signal_index]
    context.chat_data['signal_index'] = signal_index + 1  # Инкрементируем

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

    await update.message.reply_text(message_text, reply_markup=reply_markup)

async def follow_coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Функция отслеживания монеты временно недоступна.")

async def stop_tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функция остановки отслеживания временно недоступна.")
