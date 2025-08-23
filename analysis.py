import logging
import json
import os
from datetime import datetime
import pytz

from crypto_utils import get_all_coin_data
from crypto_list import TELEGRAM_WALLET_COIN_IDS

logger = logging.getLogger(__name__)

EXCLUDE_IDS = {"tether", "bitcoin", "toncoin", "binancecoin", "ethereum"}
ANALYSIS_LOG = []
RISK_GUARD_FILE = "risk_guard.json"
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


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
        with open(RISK_GUARD_FILE, "r") as f:
            data = json.load(f)
        if data.get("date") != today:
            return {"date": today, "stops": 0, "targets": 0}
        return {"date": today, "stops": int(data.get("stops", 0)), "targets": int(data.get("targets", 0))}
    except Exception:
        return {"date": today, "stops": 0, "targets": 0}


def evaluate_coin(coin):
    # Базовые поля
    rsi = round(safe_float(coin.get("rsi")), 2)
    ma7 = round(safe_float(coin.get("ma7")), 4)
    ma30 = round(safe_float(coin.get("ma30")), 4)
    price = safe_float(coin.get("current_price"))
    change_24h = round(safe_float(coin.get("price_change_percentage_24h")), 2)
    change_7d = safe_float(coin.get("price_change_percentage_7d"))
    if change_7d is not None:
        change_7d = round(change_7d, 2)
    volume = safe_float(coin.get("total_volume"))

    reasons = []
    score = 0

    # 1) RSI — «здоровая зона»
    if 50 <= rsi <= 65:
        score += 1
        reasons.append(f"✓ RSI {rsi} (50–65, ок)")
    else:
        reasons.append(f"✗ RSI {rsi} (вне 50–65)")

    # 2) Краткосрочный тренд: цена > MA7
    if ma7 > 0 and price > ma7:
        score += 1
        reasons.append(f"✓ Цена выше MA7 ({ma7})")
    else:
        reasons.append(f"✗ Цена ниже MA7 ({ma7})")

    # 3) Среднесрочный тренд: цена > MA30 и MA7 > MA30 (аналог EMA7>EMA21)
    if ma30 > 0 and price > ma30 and ma7 > ma30:
        score += 1
        reasons.append(f"✓ Цена и MA7 выше MA30 ({ma30}) — восходящая структура")
    else:
        reasons.append(f"✗ Нет подтверждения тренда (MA30={ma30}, MA7={ma7}, цена={round(price,4)})")

    # 4) Импульс за 24ч — берём «здоровый» диапазон (2.5%–12%), отсекаем пампы
    if change_24h >= 2.5 and change_24h <= 12:
        score += 1
        reasons.append(f"✓ Рост за 24ч {growth_comment(change_24h)}")
    elif change_24h > 12:
        reasons.append(f"⛔ Похоже на перегрев: {change_24h}% за 24ч — исключено")
        return 0, 0, reasons
    else:
        reasons.append(f"✗ Рост за 24ч {growth_comment(change_24h)} (мало)")

    # 5) Недельный тренд — не хуже −5%
    if change_7d is not None:
        if change_7d > 0:
            score += 1
            reasons.append(f"✓ Тренд 7д {change_7d}%")
        elif change_7d <= -5:
            reasons.append(f"⛔ Даунтренд 7д {change_7d}% (хуже −5%) — исключено")
            return 0, 0, reasons
        else:
            reasons.append(f"⚠️ Тренд 7д {change_7d}% (слабый)")
    else:
        reasons.append("⚠️ Данные по 7д отсутствуют")

    # 6) Ликвидность — минимум 7M и не «тяжёлая» >150M
    if 7_000_000 <= volume <= 150_000_000:
        score += 1
        reasons.append(f"✓ Объём {format_volume(volume)} (ликвидность ок)")
    else:
        reasons.append(f"✗ Объём {format_volume(volume)} (вне 7M–150M)")

    # Вероятность: усиливаем вклад трендовых совпадений и убираем перегрев
    trend_stack = 0
    trend_stack += 1 if price > ma7 else 0
    trend_stack += 1 if (price > ma30 and ma7 > ma30) else 0
    trend_stack += 1 if (change_24h >= 2.5 and change_24h <= 12) else 0

    base_prob = 58
    prob = base_prob \
        + (1 if 50 <= rsi <= 65 else 0) * 4.5 \
        + (1 if price > ma7 else 0) * 6.0 \
        + (1 if (price > ma30 and ma7 > ma30) else 0) * 8.0 \
        + (min(change_24h, 12) / 12) * 6.0 \
        + (1 if 7_000_000 <= volume <= 150_000_000 else 0) * 4.0 \
        + (1 if (change_7d is not None and change_7d > 0) else 0) * 4.0

    # Бонус за «полную структуру тренда»
    if trend_stack == 3:
        prob += 4.0

    prob = round(min(prob, 92), 2)

    return score, prob, reasons


async def analyze_cryptos(fallback=True):
    global ANALYSIS_LOG
    ANALYSIS_LOG.clear()

    # 🛡️ Market-guard: проверка BTC/ETH
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
        logger.warning(f"Не удалось проверить рынок (BTC/ETH): {e}")

    # 🔒 Daily risk-guard: слишком много стопов сегодня — делаем паузу
    def _read_rg():
        today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
        if not os.path.exists(RISK_GUARD_FILE):
            return {"date": today, "stops": 0, "targets": 0}
        try:
            with open(RISK_GUARD_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") != today:
                return {"date": today, "stops": 0, "targets": 0}
            return {"date": today, "stops": int(data.get("stops", 0)), "targets": int(data.get("targets", 0))}
        except Exception:
            return {"date": today, "stops": 0, "targets": 0}

    rg = _read_rg()
    if (rg["stops"] - rg["targets"] >= 2) or (rg["stops"] >= 3):
        ANALYSIS_LOG.append(
            f"🧯 Daily guard: остановка сигналов до завтра — сегодня стопов={rg['stops']}, профитов={rg['targets']}"
        )
        logger.info(ANALYSIS_LOG[-1])
        return []

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

        # Новый жёсткий порог: 5 совпадений — «отлично», 4 — «хорошо»
        if score >= 5 or (score == 4 and prob >= 78):
            passed += 1
            coin["score"] = score
            coin["probability"] = prob
            coin["reasons"] = reasons + [get_deposit_advice(prob)]
            coin["current_price"] = round_price(safe_float(coin.get("current_price")))
            coin["price_change_percentage_24h"] = round(safe_float(coin.get("price_change_percentage_24h")), 2)
            candidates.append(coin)

    # Сначала по вероятности, затем по умеренному импульсу (не максимальный памп)
    candidates.sort(key=lambda x: (
        safe_float(x.get("probability")),
        -abs(8 - safe_float(x.get("price_change_percentage_24h")))  # ближе к 8% предпочтительнее
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

            # даже в fallback — не брать перегрев и требовать ликвидность
            if price and 2.5 <= change <= 12 and volume >= 7_000_000:
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
        f"не прошло {len(all_data) - passed - excluded}"
    )

    return top_signals
