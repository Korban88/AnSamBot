def format_signal(coin_data):
    coin = coin_data['coin']
    price = coin_data['price']
    target_price = round(price * 1.05, 4)
    stop_price = round(price * 0.965, 4)
    probability = coin_data['probability']
    change_24h = coin_data['change_24h']

    reason_lines = []

    # Причины выбора монеты — краткие пояснения
    if coin_data.get("rsi"):
        rsi = coin_data['rsi']
        if rsi < 30:
            reason_lines.append("RSI низкий — монета перепродана")
        elif rsi > 70:
            reason_lines.append("RSI высокий — возможна коррекция")
        else:
            reason_lines.append("RSI нейтрален — есть потенциал роста")

    if coin_data.get("ma7") and coin_data.get("ma20"):
        if coin_data['ma7'] > coin_data['ma20']:
            reason_lines.append("MA7 выше MA20 — восходящий тренд")
        else:
            reason_lines.append("MA7 ниже MA20 — тренд слабый")

    if change_24h > 0:
        reason_lines.append("Цена растёт второй день подряд")
    elif change_24h < -3:
        reason_lines.append("Недавнее падение — возможный откат")
    else:
        reason_lines.append("Изменение цены в пределах нормы")

    reasons = "\n".join(reason_lines)

    return (
        f"💰 Ежедневный сигнал:\n"
        f"Монета: <b>{coin}</b>\n"
        f"Цена: <b>{price}$</b>\n"
        f"Рост за 24ч: <b>{round(change_24h, 2)}%</b>\n"
        f"🟢 Вероятность роста: <b>{probability}%</b>\n"
        f"🎯 Цель: <b>{target_price}$</b> (+5%)\n"
        f"⛔️ Стоп-лосс: <b>{stop_price}$</b> (−3.5%)\n\n"
        f"📊 Причины выбора:\n{reasons}"
    )
