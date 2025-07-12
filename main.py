async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(get_prices|get_top3)$"))

    logger.info("🚀 Бот запущен")
    await app.run_polling()
