import random
import logging
from analysis import analyze_cryptos
from crypto_list import CRYPTO_LIST
from crypto_utils import fetch_all_coin_data

_signal_index = 0

def reset_signal_index():
    global _signal_index
    _signal_index = 0

async def get_next_signal_message():
    global _signal_index

    try:
        top_signals = await analyze_cryptos()

        if not top_signals or _signal_index >= len(top_signals):
            reset_signal_index()
            raise Exception("Сигналы закончились или не найдены.")

        signal = top_signals[_signal_index]
        _signal_index += 1

        coin_id = signal["id"]
        entry_price = signal["entry_price"]
        target_price = signal["target_price"]
        stop_loss = signal["stop_loss"]
        probability = signal["probability"]

        message = (
            f"💹 <b>{coin_id.upper()}</b>\n\n"
            f"🎯 Цель: +5%\n"
            f"🔹 Вход: {entry_price}\n"
            f"📈 Цель: {target_price}\n"
            f"🛡 Стоп: {stop_loss}\n"
            f"📊 Вероятность роста: {probability}%"
        )

        return message, coin_id, entry_price

    except Exception as e:
        logging.error(f"Ошибка при получении сигнала: {e}")
        raise
