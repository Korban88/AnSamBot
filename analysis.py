# analysis.py
import logging
import json
import os
from datetime import datetime
import pytz

from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

# === NEW ===
from config import (
    ENABLE_FNG, ENABLE_NEWS,
    FNG_EXTREME_GREED, FNG_EXTREME_FEAR,
    MARKET_GUARD_BTC_DROP,
    NEGATIVE_TREND_7D_CUTOFF,
    PUMP_CUTOFF_24H,
    MIN_LIQUIDITY_USD, MAX_LIQUIDITY_USD
)
from sentiment_utils import get_fear_greed, get_news_sentiment  # оставляем как у тебя

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []
RISK_GUARD_FILE = "risk_guard.json"
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# === NEW: ограничиваем сколько раз за один прогон ходим за новостями ===
NEWS_MAX_PER_RUN = 5  # было 10 — уменьшаем, чтобы не ловить 429

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
    change_24h = round(change_24h, 2)
    if change_24h >= 10:
        return f"{change_24h}% 🚀 (очень высокий, возможен перегрев)"
    elif change_24h >= 5:
        return f"{change_24h}% ✅ (хороший импульс)"
    elif change_24h >= 2:
        return f"{change_24h}% (умеренный, безопасный)"
    else:
        return f"{change_24h}% ⚠️ (слабый рост)"

def _read_risk_guard():
    """Читает дневную статистику стопов/профитов для защитного режима."""
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
    if not os.path.exists(RISK_GUARD_FILE):
        return {"date": today, "stops": 0, "targets": 0}
    try:
        with open(RISK_GUARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") != today:
            return {"date": today, "stops": 0, "targets": 0}
        return {"date": today, "stops": int(data.get("stops", 0)), "targets": int(data.get("targets", 0))}
    except Exception:
        return {"date": today, "stops": 0, "targets": 0}

def evaluate_coin(coin, fng=None, news_score=None):
    """
    ДОПОЛНЕНО:
      - fng (dict) → {'value': int, 'classification': str}
      - news_score (float|None) → [-1..+1] по CryptoPanic (агрегат)
    """
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

    # Жёсткие отсевы
    if change_24h is not None and change_24h >= PUMP_CUTOFF_24H:
        return 0, 0, [f"⛔ Перегрев за 24ч ({change_24h}%) выше {PUMP_CUTOFF_24H}% — исключено"]
    if change_7d is not None and change_7d <= NEGATIVE_TREND_7D_CUTOFF:
        return 0, 0, reasons + [f"⛔ Даунтренд за 7д {change_7d}% ≤ {NEGATIVE_TREND_7D_CUTOFF}% — исключено"]
    if volume is not None and not (MIN_LIQUIDITY_USD <= volume <= MAX_LIQUIDITY_USD):
        return 0, 0, reasons + [f"⛔ Объём {format_volume(volume)} вне допустимого диапазона"]

    # RSI
    if 52 <= rsi <= 60:
        score += 1
        reasons.append(f"✓ RSI {rsi} (в норме)")
    else:
        reasons.append(f"✗ RSI {rsi} (вне диапазона 52–60)")

    # MA7
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"✓ Цена выше MA7 ({ma7})")
    else:
        reasons.append(f"✗ Цена ниже MA7 ({ma7})")

    # 24h
    if change_24h >= 2.5:
        score += 1
        reasons.append(f"✓ Рост за 24ч {growth_comment(change_24h)}")
    else:
        reasons.append(f"✗ Рост за 24ч {growth_comment(change_24h)}")

    # 7d
    if change_7d is not None:
        if change_7d > 0:
            score += 1
            reasons.append(f"✓ Тренд за 7д {change_7d}%")
        else:
            reasons.append(f"✗ Тренд за 7д {change_7d}% (просадка)")
    else:
        reasons.append("⚠️ Данные по 7д отсутствуют")

    # Объём — до этого уже отфильтровали допустимый диапазон
    score += 1
    reasons.append(f"✓ Объём {format_volume(volume)}")

    # База вероятности
    rsi_weight = 1 if 52 <= rsi <= 60 else 0
    ma_weight = 1 if ma7 > 0 and price > ma7 else 0
    change_weight = min(change_24h / 6, 1) if change_24h > 0 else 0
    vol_weight = 1
    trend_weight = 1 if (change_7d is not None and change_7d > 0) else 0

    base_prob = 60
    prob = base_prob + (rsi_weight + ma_weight + change_weight + vol_weight + trend_weight) * 5

    # Fear & Greed
    if fng and isinstance(fng.get("value", None), int):
        fng_val = fng["value"]
        fng_cls = fng.get("classification", "")
        if fng_val >= FNG_EXTREME_GREED:
            prob -= 2
            reasons.append(f"🧭 F&G: {fng_val} ({fng_cls}) — осторожнее")
        elif fng_val <= FNG_EXTREME_FEAR:
            prob -= 2
            reasons.append(f"🧭 F&G: {fng_val} ({fng_cls}) — осторожнее")

    # Новости
    if news_score is not None:
        if news_score > 0.2:
            prob = min(prob + 2, 92)
            reasons.append("📰 Позитивный новостной фон")
        elif news_score < -0.2:
            prob = max(prob - 3, 0)
            reasons.append("📰 Негативный новостной фон")

    # Мягкая корректировка 7д
    if change_7d is not None:
        if change_7d >= 3:
            prob = min(prob + 1, 92)
        elif change_7d < 0:
            prob = max(prob - 1, 0)

    prob = round(min(prob, 92), 2)
    return score, prob, reasons

async def analyze_cryptos(fallback=True):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    # Market-guard: BTC/ETH
    try:
        mk = await get_all_coin_data(["bitcoin", "ethereum"])
        mk_map = {c.get("id"): c for c in mk}
        btc_24h = safe_float(mk_map.get("bitcoin", {}).get("price_change_percentage_24h"))
        eth_24h = safe_float(mk_map.get("ethereum", {}).get("price_change_percentage_24h"))
        # ВАЖНО: защита должна срабатывать только при падении BTC на заданное значение
        if btc_24h <= -abs(MARKET_GUARD_BTC_DROP):
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
        logger.warning(f"Не удалось проверить рынок (BTC/ETH): {e}")

    # Fear & Greed
    fng = None
    if ENABLE_FNG:
        try:
            fng = await get_fear_greed()
            if fng:
                ANALYSIS_LOG.append(f"🧭 Fear&Greed: {fng['value']} ({fng.get('classification','')})")
        except Exception as e:
            logger.warning(f"F&G недоступен: {e}")

    # Daily risk-guard
    rg = _read_risk_guard()
    if (rg["stops"] - rg["targets"] >= 2) or (rg["stops"] >= 3):
        ANALYSIS_LOG.append(
            f"🧯 Daily guard: остановка сигналов до завтра — сегодня стопов={rg['stops']}, профитов={rg['targets']}"
        )
        logger.info(ANALYSIS_LOG[-1])
        return []

    # Данные по монетам
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

    news_calls = 0  # === NEW: считаем, сколько раз сходили за новостями

    for coin in all_data:
        coin_id = coin.get("id", "")
        if coin_id in EXCLUDE_IDS:
            excluded += 1
            continue

        # первичная оценка без дорогих вызовов новостей
        try:
            score, prob, reasons = evaluate_coin(coin, fng=fng, news_score=None)
        except Exception:
            continue

        # новости — только для претендентов и в пределах лимита NEWS_MAX_PER_RUN
        news_score = None
        if ENABLE_NEWS and score >= 3 and news_calls < NEWS_MAX_PER_RUN:
            try:
                sym = (coin.get("symbol") or "").upper()
                news_score = await get_news_sentiment(sym or coin_id, ttl=3600)  # кэш до 1 часа
                news_calls += 1
                # пересчёт с учётом новостей
                score, prob, reasons = evaluate_coin(coin, fng=fng, news_score=news_score)
                if news_score is not None:
                    ANALYSIS_LOG.append(f"📰 {sym or coin_id}: news_score={round(news_score,2)}")
            except Exception as e:
                logger.warning(f"Новости недоступны для {coin_id}: {e}")

        if score >= 4:
            passed += 1
            coin["score"] = score
            coin["probability"] = prob
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
        f"📊 Статистика анализа: получено {len(all_data)} из {len(coin_ids)}, "
        f"прошло фильтр {passed}, без данных {no_data}, исключено {excluded}, "
        f"не прошло {len(all_data) - passed - excluded}; news_calls={news_calls}/{NEWS_MAX_PER_RUN}"
    )

    return top_signals
