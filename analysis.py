from crypto_utils import get_market_data
from crypto_list import MONITORED_SYMBOLS
import json
import random

used_symbols_file = "used_symbols.json"

def load_used_symbols():
    try:
        with open(used_symbols_file, "r") as f:
            return json.load(f)
    except:
        return []

def save_used_symbols(symbols):
    with open(used_symbols_file, "w") as f:
        json.dump(symbols[-6:], f)

async def get_top_signal():
    data = await get_market_data()
    signals = []

    for item in data:
        symbol = item["symbol"].upper()
        if symbol not in MONITORED_SYMBOLS:
            continue

        rsi = item.get("rsi")
        ma = item.get("ma")
        change = item.get("price_change_percentage_24h")
        price = item.get("current_price")

        if not all([rsi, ma, change, price]):
            continue

        if change < -3 or rsi > 70 or ma > price:
            continue

        probability = round(100 - abs(rsi - 50) - abs(price - ma) / price * 100 - abs(change) * 2)
        if probability >= 65:
            signals.append({
                "symbol": symbol,
                "entry_price": round(price, 4),
                "target_price": round(price * 1.05, 4),
                "stop_loss": round(price * 0.97, 4),
                "probability": probability,
                "change_24h": round(change, 2)
            })

    if not signals:
        return None

    signals.sort(key=lambda x: x["probability"], reverse=True)
    used = load_used_symbols()
    for signal in signals:
        if signal["symbol"] not in used:
            used.append(signal["symbol"])
            save_used_symbols(used)
            return signal

    return None
