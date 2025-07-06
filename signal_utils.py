import random
from analysis import analyze_cryptos

signal_index = 0

async def get_next_signal_message():
    global signal_index

    top_cryptos = await analyze_cryptos()

    if not top_cryptos:
        return "⚠️ Не удалось получить сигналы.", None, None

    coin = top_cryptos[signal_index % len(top_cryptos)]
    signal_index += 1

    symbol = coin["symbol"].upper()
    entry = coin["entry_price"]
    target = coin["target_price"]
    stop = coin["stop_loss"]
    probability = coin["probability"]
    explanation = coin["explanation"]

    message = (
        f"🚀 *Сигнал на рост: {symbol}*\n\n"
        f"*📈 Цель:* +5% (до {target:.4f}$)\n"
        f"*💰 Вход:* {entry:.4f}$\n"
        f"*🛑 Стоп:* {stop:.4f}$\n"
        f"*📊 Вероятность:* {probability:.1f}%\n\n"
        f"📎 _{explanation}_"
    )

    return message, coin["id"], entry

def reset_signal_index():
    global signal_index
    signal_index = 0
