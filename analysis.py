import logging
from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def round_price(price):
    if price >= 1:
        return round(price, 3)
    elif price >= 0.01:
        return round(price, 4)
    else:
        return round(price, 6)


def format_volume(volume):
    if volume >= 1_000_000_000:
        return f"{round(volume / 1_000_000_000, 2)}B"
    elif volume >= 1_000_000:
        return f"{round(volume / 1_000_000, 2)}M"
    elif volume >= 1_000:
        return f"{round(volume / 1_000, 2)}K"
    else:
        return str(volume)


def get_deposit_advice(prob):
    if prob >= 85:
        return "💰 Совет: можно вложить до 35% депозита (очень сильный сигнал)"
    elif prob >= 75:
        return "💰 Совет: не более 25% депозита (сильный сигнал)"
    else:
        return "💰 Совет: не более 15–20% депозита (умеренный сигнал)"


def growth_comment(change_24h):
    change_24h = round(change_24h, 2)  # округляем всегда до 2 знаков
    if change_24h >= 10:
        return f"{change_24h}% 🚀 (очень высокий, возможен перегрев)"
    elif change_24h >= 5:
        return f"{change_24h}% ✅ (хороший импульс)"
    elif change_24h >= 2:
        return f"{change_24h}% (умеренный, безопасный)"
    else:
        return f"{change_24h}% ⚠️ (слабый рост)"


def evaluate_coin(coin):
    rsi = round(safe_float(coin.get("rsi")), 2)
    ma7 = round(safe_float(coin.get("ma7")), 4)
    price = safe_float(coin.get("current_price"))
    change_24h = round(safe_float(coin.get("price_change_percentage_24h")), 2)
    change_7d = safe_float(coin.get("price_change_percentage_7d"))
    if change_7d is not None:
        change_7d = round(change_7d, 2)
    volume = safe_float(coin.get("total_volume"))
    symbol = coin.get("symbol", "?").upper()

    reasons = []
    score = 0

    # RSI check
    if 52 <= rsi <= 60:
        score += 1
        reasons.append(f"✓ RSI {rsi} (в норме)")
    else:
        reasons.append(f"✗ RSI {rsi} (вне диапазона 52–60)")

    # MA7 check
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"✓ Цена выше MA7 ({ma7})")
    else:
        reasons.append(f"✗ Цена ниже MA7 ({ma7})")

    # Change 24h check
    if change_24h >= 2.5:
        score += 1
        reasons.append(f"✓ Рост за 24ч {growth_comment(change_24h)}")
    else:
        reasons.append(f"✗ Рост за 24ч {growth_comment(change_24h)}")

    # Weekly trend check
    if change_7d is not None:
        if change_7d > 0:
            score += 1
            reasons.append(f"✓ Тренд за 7д {change_7d}%")
        else:
            reasons.append(f"✗ Тренд за 7д {change_7d}% (просадка)")
    else:
        reasons.append("⚠️ Данные по 7д отсутствуют")

    # Volume check
    if 5_000_000 <= volume <= 100_000_000:
        score += 1
        reasons.append(f"✓ Объём {format_volume(volume)}")
    else:
        reasons.append(f"✗ Объём {format_volume(volume)} (не в диапазоне)")

    # Probability
    rsi_weight = 1 if 52 <= rsi <= 60 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 6, 1) if change_24h > 0 else 0
    volume_weight = 1 if 10_000_000 <= volume <= 100_000_000 else 0.5 if volume >= 5_000_000 else 0
    trend_weight = 1 if change_7d and change_7d > 0 else 0

    base_prob = 60
    prob = base_prob + (rsi_weight + ma_weight + change_weight + volume_weight + trend_weight) * 5
    prob = round(min(prob, 92), 2)

    return score, prob, reasons


async def analyze_cryptos(fallback=True):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    # 🛡️ Market-guard: если BTC падает сильнее -2% за 24ч — не торгуем
    try:
        mk = await get_all_coin_data(["bitcoin", "ethereum"])
        mk_map = {c.get("id"): c for c in mk}
        btc_24h = safe_float(mk_map.get("bitcoin", {}).get("price_change_percentage_24h"))
        eth_24h = safe_float(mk_map.get("ethereum", {}).get("price_change_percentage_24h"))
        if btc_24h <= -2.0:
            ANALYSIS_LOG.append(
                f"🛑 Рынок слабый: BTC {round(btc_24h,2)}%, ETH {round(eth_24h,2)}% за 24ч — сигналы отключены"
            )
            logger.info(ANALYSIS_LOG[-1])
            return []
        else:
            ANALYSIS_LOG.append(
                f"🟢 Рынок ок: BTC {round(btc_24h,2)}%, ETH {round(eth_24h,2)}% — продолжаем анализ"
            )
    except Exception as e:
        # Если не удалось проверить рынок — продолжаем, но логируем
        logger.warning(f"Не удалось проверить рынок (BTC/ETH): {e}")

    try:
        coin_ids = list(TELEGRAM_WALLET_COIN_IDS.keys())
        all_data = await get_all_coin_data(coin_ids)
        logger.info(f"📊 Данные получены по {len(all_data)} монетам из {len(coin_ids)}")

        missing_ids = set(coin_ids) - {c.get("id") for c in all_data}
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []

    candidates = []
    passed = 0
    no_data = len(missing_ids)
    excluded = 0

    for coin in all_data:
        coin_id = coin.get("id", "")
        if coin_id in EXCLUDE_IDS:
            excluded += 1
            continue

        try:
            score, prob, reasons = evaluate_coin(coin)
        except Exception:
            continue

        if score >= 4:
            passed += 1
            coin["score"] = score
            coin["probability"] = prob
            # добавим маркер про рынок в reasons, если он был рассчитан выше
            coin["reasons"] = reasons + [get_deposit_advice(prob)]
            coin["current_price"] = round_price(safe_float(coin.get("current_price")))
            coin["price_change_percentage_24h"] = round(safe_float(coin.get("price_change_percentage_24h")), 2)
            candidates.append(coin)

    candidates.sort(key=lambda x: (
        safe_float(x.get("probability")),
        safe_float(x.get("price_change_percentage_24h"))
    ), reverse=True)

    top_signals = []
    for coin in candidates[:6]:
        signal = {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "current_price": coin["current_price"],
            "price_change_percentage_24h": coin["price_change_percentage_24h"],
            "probability": coin["probability"],
            "reasons": coin["reasons"],
            "safe": True
        }
        top_signals.append(signal)

    if not top_signals and fallback:
        all_data.sort(key=lambda x: safe_float(x.get("price_change_percentage_24h")), reverse=True)
        for fallback_coin in all_data:
            if fallback_coin.get("id") in EXCLUDE_IDS:
                continue
            price = round_price(safe_float(fallback_coin.get("current_price")))
            change = round(safe_float(fallback_coin.get("price_change_percentage_24h")), 2)
            volume = safe_float(fallback_coin.get("total_volume", 0))

            if price and change and volume >= 3_000_000:
                top_signals.append({
                    "id": fallback_coin["id"],
                    "symbol": fallback_coin["symbol"],
                    "current_price": price,
                    "price_change_percentage_24h": change,
                    "probability": 65.0,
                    "reasons": ["⚠️ Fallback: рискованный выбор (нет идеальных монет)", get_deposit_advice(65)],
                    "safe": False
                })
                break

    ANALYSIS_LOG.append(
        f"📊 Статистика анализа: получено {len(all_data)} из {len(TELEGRAM_WALLET_COIN_IDS)}, "
        f"прошло фильтр {passed}, без данных {no_data}, исключено {excluded}, "
        f"не прошло {len(all_data) - passed - excluded}"
    )

    return top_signals
