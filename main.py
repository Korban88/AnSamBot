import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, OWNER_ID
from analysis import analyze_cryptos
from tracking import start_tracking_coin, stop_all_tracking

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📈 Получить сигнал", callback_data="get_signal")]]
    if str(update.effective_user.id) == str(OWNER_ID):
        keyboard.append([InlineKeyboardButton("⛔ Остановить все отслеживания", callback_data="stop_tracking")])
    await update.message.reply_text(
        "Добро пожаловать в новую жизнь, Корбан!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_signal":
        await get_signal(update, context)
    elif query.data.startswith("track:"):
        coin_id = query.data.split(":", 1)[1]
        await start_tracking_coin(context.bot, coin_id, OWNER_ID)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"📍 Монета `{coin_id}` теперь отслеживается на рост +3.5% и +5%", parse_mode=ParseMode.MARKDOWN_V2)
    elif query.data == "stop_tracking":
        stop_all_tracking()
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("⛔ Все отслеживания остановлены.")


async def get_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = analyze_cryptos()
    if not coins:
        await update.callback_query.message.reply_text("⚠️ Нет подходящих монет для сигнала.")
        return

    coin = coins[0]
    entry_price = coin['current_price']
    target_price = round(entry_price * 1.05, 4)
    stop_loss_price = round(entry_price * 0.97, 4)
    growth_prob = coin.get('growth_probability', 0)

    message = (
        f"*🟢 Сигнал на рост: {coin['id'].capitalize()}*\n"
        f"Цена входа: *${entry_price}*\n"
        f"Цель: *${target_price}* (+5%)\n"
        f"Стоп-лосс: *${stop_loss_price}*\n"
        f"Вероятность роста: *{growth_prob}%*\n"
    )
    keyboard = [[InlineKeyboardButton("📍 Следить за монетой", callback_data=f"track:{coin['id']}")]]
    await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
