from analysis import analyze_cryptos
from crypto_utils import fetch_all_coin_data
from crypto_list import CRYPTO_LIST

signal_index = 0

async def get_next_signal_message():
    global signal_index
    coin_data_list = await fetch_all_coin_data([coin_id])
    coin_data = coin_data_list[0]  # потому что возвращается список
    top_3 = await analyze_cryptos(coin_data)

    if not top_3:
        raise Exception("Нет подходящих монет для сигнала")

    coin = top_3[signal_index % len(top_3)]
    signal_index += 1

    coin_id = coin["id"]
    probability = coin["probability"]
    entry_price = coin["entry_price"]
    target_price = coin["target_price"]
    stop_loss_price = coin["stop_loss_price"]
    rsi = coin["rsi"]
    ma = coin["ma"]
    change_24h = coin["change_24h"]

    message = (
        f"📈 <b>Сигнал на рост</b>\n\n"
        f"Монета: <b>{coin_id}</b>\n"
        f"Цена входа: <code>{entry_price}</code>\n"
        f"Цель +5%: <code>{target_price}</code>\n"
        f"Стоп-лосс: <code>{stop_loss_price}</code>\n"
        f"Вероятность роста: <b>{probability:.1f}%</b>\n\n"
        f"<b>Обоснование:</b>\n"
        f"• RSI: {rsi} — индикатор перекупленности/перепроданности\n"
        f"• MA: {ma} — скользящая средняя\n"
        f"• 24ч изменение: {change_24h}%"
    )

    return message, coin_id, entry_price

def reset_signal_index():
    global signal_index
    signal_index = 0
