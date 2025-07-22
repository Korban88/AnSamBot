import json
from crypto_utils import get_market_data
from crypto_list import MONITORED_SYMBOLS

USED_SYMBOLS_FILE = "used_symbols.json"

def load_used_symbols():
    try:
        with open(USED_SYMBOLS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_used_symbols(symbols):
    with open(USED_SYMBOLS_FILE, "w") as f:
        json.dump(symbols[-6:], f)

async def get_top_signal():
    signals = []

    for symbol in MONITORED_SYMBOLS:
        data = await get_market_data(symbol)
        if not data:
            continue

        rsi = data.get("rsi")
        ma = data.get("ma")
        change = data.get("change_24h")
        price = data.get("price")

        if not all([rsi, ma, change, price]):
            continue

        if change < -3 or rsi > 70 or ma > price:
            continue

        # Улучшенная формула вероятности
        rsi_score = max(0, 20 - abs(rsi - 50))  # до 20
        trend_score = max(0, 30 - abs(ma - price) / price * 100)  # до 30
        change_score = max(0, 30 - abs(change) * 2)  # до 30

        probability = round(50 + rsi_score + trend_score + change_score)
        if probability > 100:
            probability = 100

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
