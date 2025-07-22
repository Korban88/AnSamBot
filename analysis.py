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
            continue

        price = data.get("price")
        change = data.get("change_24h")
        rsi = data.get("rsi")
        volume = data.get("volume_24h")
        volat = data.get("volatility")
        vol_growth = data.get("volume_growth")

        if not all([price, change, rsi, volume, volat, vol_growth]):
            continue

        # Жёсткие условия взрывного роста
        if volume < 2_000_000:  # низкий объём
            continue
        if change < -4:  # сильное падение — риск
            continue
        if vol_growth < 20:  # объём не растёт — нет импульса
            continue
        if volat < 4:  # нет волатильности — неинтересно
            continue
        if rsi > 70:  # перекуплен
            continue

        # Формула оценки взрывного потенциала
        score = 0
        if 40 < rsi < 60: score += 20
        if vol_growth >= 50: score += 25
        if volat >= 6: score += 25
        if change >= 1: score += 10
        if 3 <= volat < 6: score += 10
        if rsi < 40: score += 5  # отскок возможен

        probability = min(90, 50 + score)

        if probability >= 65:
            signals.append({
                "symbol": symbol,
                "entry_price": round(price, 4),
                "target_price": round(price * 1.07, 4),
                "stop_loss": round(price * 0.94, 4),
                "probability": probability,
                "change_24h": round(change, 2),
                "volume_growth": round(vol_growth, 1),
                "volatility": round(volat, 2)
            })

    if not signals:
        print("❌ Нет агрессивных кандидатов на памп.")
        return None

    signals.sort(key=lambda x: x["probability"], reverse=True)

    for signal in signals:
        if signal["symbol"] not in used:
            used.append(signal["symbol"])
            save_used_symbols(used)
            print(f"📢 Сигнал: {signal['symbol']} → вероятность {signal['probability']}%")
            return signal

    print("🔁 Все подходящие монеты уже использованы.")
    return None
