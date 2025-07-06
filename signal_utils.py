def format_signal_message(symbol, entry_price, target_price, stop_loss_price, growth_probability, explanation):
    return (
        f"*📈 Сигнал на покупку {symbol.upper()}*\n"
        f"▪️ Вход: `{entry_price}`\n"
        f"🎯 Цель (+5%): `{target_price}`\n"
        f"⛔ Стоп-лосс: `{stop_loss_price}`\n"
        f"🔮 Вероятность роста: *{growth_probability:.1f}%*\n\n"
        f"{explanation}"
    )
