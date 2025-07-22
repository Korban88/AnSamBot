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
    used = load_used_symbols()

    for symbol in MONITORED_SYMBOLS:
        if symbol in used:
            continue

        data = await get_market_data(symbol)
        if not data:
            print(f"⚠️ {symbol}: нет данных с API")
            continue

        rsi = data.get("rsi")
        ma = data.get("ma")
        change = data.get("change_24h")
        price = data.get("price")

        if not all([rsi, ma, change, price]):
            print(f"⚠️ {symbol}: отсутствуют ключевые метрики")
            continue

        # Строгий фильтр — отсеиваем сомнительные монеты
        if change < -5:
            print(f"⛔ {symbol} исключён: падение {change:.2f}%")
            continue
        if rsi > 75 or rsi < 25:
            print(f"⛔ {symbol} исключён: RSI={rsi}")
            continue
        if ma > price * 1.05:
            print(f"⛔ {symbol} исключён: MA выше цены (MA={ma}, P={price})")
            continue

        # Улучшенная формула вероятности
        base = 40
        rsi_score = max(0, 15 - abs(rsi - 50))  # до 15
        trend_score = max(0, 25 - abs(ma - price) / price * 100)  # до 25
        change_score = max(0, 20 - abs(change) * 2)  # до 20

        probability = round(base + rsi_score + trend_score + change_score)
        probability = min(probability, 90)

        print(f"✅ {symbol} прошёл отбор: RSI={rsi}, MA={ma}, P={price}, Δ24h={change}, → {probability}%")

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
        print("❌ Нет подходящих монет среди всех доступных")
        return None

    signals.sort(key=lambda x: x["probability"], reverse=True)

    # Первая подходящая монета, не использованная ранее
    for signal in signals:
        symbol = signal["symbol"]
        if symbol not in used:
            used.append(symbol)
            save_used_symbols(used)
            print(f"📤 Сигнал выбран: {symbol} с вероятностью {signal['probability']}%")
            return signal

    print("🔁 Все топ монеты уже использовались")
    return None
