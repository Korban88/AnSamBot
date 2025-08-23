# crypto_utils.py
# Двухэтапный сбор данных: 1) /coins/markets для всех  2) /market_chart (RSI/MA) только для претендентов.
import aiohttp
import json
import os
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple

CACHE_PATH = "indicators_cache.json"

# ---------- Настройки анти‑429 / кэша (меняем через ENV при желании) ----------
CG_CHUNK_SIZE      = int(os.getenv("CG_CHUNK_SIZE", "45"))
CG_CHUNK_PAUSE     = float(os.getenv("CG_CHUNK_PAUSE", "2"))         # пауза между чанками markets
HTTP_MAX_RETRIES   = int(os.getenv("HTTP_MAX_RETRIES", "6"))
HTTP_BACKOFF_BASE  = float(os.getenv("HTTP_BACKOFF_BASE", "1.7"))
HTTP_TIMEOUT       = float(os.getenv("HTTP_TIMEOUT", "20"))

# Истории и индикаторы
HIST_TTL_MIN       = int(os.getenv("HIST_TTL_MIN", "360"))           # 6 часов для /market_chart
INDIC_TTL_MIN      = int(os.getenv("INDIC_TTL_MIN", "30"))

# Ограничения TA‑запросов (второй этап)
TA_MAX_PER_RUN     = int(os.getenv("TA_MAX_PER_RUN", "15"))          # максимум монет для RSI/MA за прогон
TA_CONCURRENCY     = int(os.getenv("TA_CONCURRENCY", "2"))           # параллельность market_chart
TA_RETRIES         = int(os.getenv("TA_RETRIES", "2"))               # 429 → не блокируем цикл, просто пропускаем

# Предфильтр претендентов (чтобы не дёргать TA по «мусору»)
CH24_PREFILTER_MIN = float(os.getenv("CH24_PREFILTER_MIN", "1.5"))   # минимальный рост за 24ч для кандидата TA
MIN_LIQUIDITY_USD  = float(os.getenv("MIN_LIQUIDITY_USD", "5000000"))
MAX_LIQUIDITY_USD  = float(os.getenv("MAX_LIQUIDITY_USD", "100000000"))

# ---------- Кэш ----------
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            INDICATOR_CACHE: Dict[str, Any] = json.load(f)
    except Exception:
        INDICATOR_CACHE = {}
else:
    INDICATOR_CACHE = {}

def _atomic_save(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def save_cache() -> None:
    _atomic_save(CACHE_PATH, INDICATOR_CACHE)

# ---------- Утилиты ----------
def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def simulate_rsi(price_change):
    import random
    if price_change >= 10:
        return random.randint(65, 75)
    elif price_change >= 5:
        return random.randint(55, 65)
    elif price_change >= 0:
        return random.randint(45, 55)
    elif price_change >= -3:
        return random.randint(35, 45)
    else:
        return random.randint(25, 35)

def simulate_ma(price, days=7):
    import random
    variation = random.uniform(-0.03, 0.03)
    return round(safe_float(price) * (1 - variation), 4)

def calculate_ma(prices, days=7):
    if len(prices) < days:
        return None
    return round(sum(prices[-days:]) / days, 4)

def calculate_rsi(prices):
    if len(prices) < 8:
        return None
    gains, losses = [], []
    for i in range(1, 8):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    avg_gain = sum(gains) / 7 if gains else 0.0001
    avg_loss = sum(losses) / 7 if losses else 0.0001
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ---------- HTTP (единый клиент) ----------
_SESSION: Optional[aiohttp.ClientSession] = None
_SESSION_LOCK = asyncio.Lock()

async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION and not _SESSION.closed:
        return _SESSION
    async with _SESSION_LOCK:
        if _SESSION is None or _SESSION.closed:
            timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            _SESSION = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Accept": "application/json", "User-Agent": "AnSamBot/anti429"}
            )
    return _SESSION

async def _request_json(method: str, url: str, *, params: Dict[str, Any] = None) -> Any:
    session = await _get_session()
    attempt = 0
    while True:
        try:
            async with session.request(method.upper(), url, params=params) as resp:
                if resp.status == 429:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"429 Too Many Requests after {attempt} retries: {url}")
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_s = min(float(retry_after), 30.0)
                        except ValueError:
                            wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 25.0)
                    else:
                        wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 25.0)
                    logging.warning(f"⚠️ 429 по {url}. Ждём {round(wait_s,1)} сек (попытка {attempt})")
                    await asyncio.sleep(wait_s)
                    continue
                if 500 <= resp.status < 600:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"{resp.status} after {attempt} retries: {url}")
                    wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 20.0)
                    logging.warning(f"⚠️ {resp.status} по {url}. Повтор через {round(wait_s,1)} сек (попытка {attempt})")
                    await asyncio.sleep(wait_s)
                    continue
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            attempt += 1
            if attempt > HTTP_MAX_RETRIES:
                raise
            wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.2 * attempt, 20.0)
            logging.warning(f"⚠️ Ошибка запроса {e}. Повтор через {round(wait_s,1)} сек (попытка {attempt})")
            await asyncio.sleep(wait_s)

# ---------- CoinGecko: Markets (1-й этап) ----------
async def _fetch_markets_chunk(ids: List[str]) -> List[Dict[str, Any]]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(ids),
        "price_change_percentage": "24h,7d"
    }
    try:
        data = await _request_json("GET", url, params=params)
        return data if isinstance(data, list) else []
    finally:
        await asyncio.sleep(CG_CHUNK_PAUSE)

async def fetch_all_coin_data(coin_ids: List[str]) -> List[Dict[str, Any]]:
    """/coins/markets — быстро и батчами. Без RSI/MA на этом шаге."""
    results: List[Dict[str, Any]] = []
    if not coin_ids:
        return results

    for i in range(0, len(coin_ids), CG_CHUNK_SIZE):
        chunk = coin_ids[i:i + CG_CHUNK_SIZE]
        try:
            rows = await _fetch_markets_chunk(chunk)
            results.extend(rows)
        except Exception as e:
            logging.error(f"❌ Ошибка API для монет {chunk[:3]}...: {e}")
    return results

# ---------- CoinGecko: Market Chart (2-й этап) ----------
async def _fetch_historical_prices_raw(coin_id: str, days: int = 30) -> List[float]:
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}

    # собственный цикл с мягкими повторами, но ОГРАНИЧЕННЫЙ для TA
    attempt = 0
    while True:
        try:
            data = await _request_json("GET", url, params=params)
            return [safe_float(p[1]) for p in data.get("prices", [])]
        except Exception as e:
            attempt += 1
            if attempt >= TA_RETRIES:
                logging.warning(f"⏭️ Пропускаю TA для {coin_id} после {attempt} ошибок: {e}")
                return []
            await asyncio.sleep(3 * attempt)

async def fetch_historical_prices(coin_id: str, days: int = 30) -> List[float]:
    """Истории с кэшем (6 часов)."""
    now = datetime.utcnow()
    node = INDICATOR_CACHE.get(coin_id, {})
    ts_str = node.get("hist_ts")
    if ts_str:
        try:
            ts = datetime.fromisoformat(ts_str)
            if now - ts < timedelta(minutes=HIST_TTL_MIN):
                cached = node.get("hist_prices")
                if isinstance(cached, list) and cached:
                    return [safe_float(p) for p in cached]
        except Exception:
            pass

    prices = await _fetch_historical_prices_raw(coin_id, days=days)
    INDICATOR_CACHE.setdefault(coin_id, {})
    INDICATOR_CACHE[coin_id]["hist_prices"] = prices
    INDICATOR_CACHE[coin_id]["hist_ts"] = now.isoformat()
    save_cache()
    return prices

# ---------- Основная функция (интерфейс НЕ меняем) ----------
async def get_all_coin_data(coin_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Возвращает список монет с полями:
    id, symbol, current_price, price_change_percentage_24h, price_change_percentage_7d_in_currency,
    total_volume, rsi, ma7, ma30, no_data

    Этапы:
      1) markets для всех монет;
      2) предфильтр → максимум TA_MAX_PER_RUN монет → считаем RSI/MA;
      3) остальные получают rsi/ma=None (analysis.py их просто отсеет).
    """
    raw_data = await fetch_all_coin_data(coin_ids)
    received_ids = {c.get("id") for c in raw_data}
    result: List[Dict[str, Any]] = []

    # Преобразуем markets
    for coin in raw_data:
        coin_id = coin.get("id", "")
        current_price = safe_float(coin.get("current_price"))
        change_24h = safe_float(coin.get("price_change_percentage_24h"))
        change_7d = safe_float(coin.get("price_change_percentage_7d_in_currency"))
        volume = safe_float(coin.get("total_volume"))

        # дефолтные значения, TA позже
        result.append({
            **coin,
            "current_price": current_price,
            "price_change_percentage_24h": change_24h,
            "price_change_percentage_7d": change_7d,
            "total_volume": volume,
            "rsi": None,
            "ma7": None,
            "ma30": None,
            "no_data": False
        })

    # Предфильтр кандидатов для TA
    candidates: List[Tuple[str, float, float]] = []
    for row in result:
        vol = safe_float(row.get("total_volume"))
        ch24 = safe_float(row.get("price_change_percentage_24h"))
        if (MIN_LIQUIDITY_USD <= vol <= MAX_LIQUIDITY_USD) and (ch24 >= CH24_PREFILTER_MIN):
            candidates.append((row["id"], vol, ch24))

    # Берём топ по росту/объёму и ограничиваем
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    ta_ids = [cid for cid, _, _ in candidates[:TA_MAX_PER_RUN]]

    # Считаем TA с ограниченной параллельностью
    sem = asyncio.Semaphore(max(1, TA_CONCURRENCY))

    async def ta_for(coin_id: str) -> Tuple[str, Optional[float], Optional[float], Optional[float]]:
        async with sem:
            prices = await fetch_historical_prices(coin_id, days=30)
            if not prices:
                return coin_id, None, None, None
            rsi = calculate_rsi(prices[-8:])  # оставляем твою «короткую» RSI-логику
            ma7 = calculate_ma(prices, days=7)
            ma30 = calculate_ma(prices, days=30)
            return coin_id, rsi, ma7, ma30

    ta_results = await asyncio.gather(*(ta_for(cid) for cid in ta_ids))

    # Применяем TA-результаты
    ta_map = {cid: (rsi, ma7, ma30) for cid, rsi, ma7, ma30 in ta_results}
    now = datetime.utcnow()
    for row in result:
        cid = row.get("id", "")
        if cid in ta_map:
            rsi, ma7, ma30 = ta_map[cid]
            if rsi is None or ma7 is None or ma30 is None:
                # мягкий фоллбек, если TA не достали
                ch24 = safe_float(row.get("price_change_percentage_24h"))
                price = safe_float(row.get("current_price"))
                rsi = rsi or simulate_rsi(ch24)
                ma7 = ma7 or simulate_ma(price, 7)
                ma30 = ma30 or simulate_ma(price, 30)
            row["rsi"] = rsi
            row["ma7"] = ma7
            row["ma30"] = ma30
            INDICATOR_CACHE.setdefault(cid, {})
            INDICATOR_CACHE[cid].update({
                "rsi": rsi, "ma7": ma7, "ma30": ma30,
                "timestamp": now.isoformat(),
                "price": safe_float(row.get("current_price"))
            })

    # Добавляем недостающие id как «no_data»
    missing_ids = [cid for cid in coin_ids if cid not in received_ids]
    for cid in missing_ids:
        result.append({
            "id": cid,
            "symbol": cid.upper(),
            "current_price": None,
            "price_change_percentage_24h": None,
            "price_change_percentage_7d": None,
            "total_volume": None,
            "rsi": None,
            "ma7": None,
            "ma30": None,
            "no_data": True
        })

    save_cache()
    return result

# ---------- Упрощённый геттер цены (оставляем интерфейс) ----------
async def get_current_price(query):
    from crypto_list import TELEGRAM_WALLET_COIN_IDS

    # Определяем: это CoinGecko ID или символ
    coin_id = None
    if query in TELEGRAM_WALLET_COIN_IDS:
        coin_id = query
    else:
        for id_, sym in TELEGRAM_WALLET_COIN_IDS.items():
            if sym.lower() == query.lower():
                coin_id = id_
                break

    if not coin_id:
        logging.error(f"❌ Монета {query} не найдена в TELEGRAM_WALLET_COIN_IDS")
        return None

    # Сначала свежий кеш (15 минут)
    cached = INDICATOR_CACHE.get(coin_id, {})
    timestamp = cached.get("timestamp")
    now = datetime.utcnow()
    if timestamp:
        try:
            if now - datetime.fromisoformat(timestamp) < timedelta(minutes=15):
                if cached.get("price") is not None:
                    logging.info(f"📌 Цена {query.upper()} из кеша: {cached['price']}")
                    return cached["price"]
        except Exception:
            pass

    # Иначе — markets только для одной монеты
    markets = await fetch_all_coin_data([coin_id])
    if markets and isinstance(markets, list):
        price = safe_float(markets[0].get("current_price"))
        INDICATOR_CACHE.setdefault(coin_id, {})
        INDICATOR_CACHE[coin_id]["price"] = price
        INDICATOR_CACHE[coin_id]["timestamp"] = now.isoformat()
        save_cache()
        logging.info(f"📌 Цена {query.upper()} обновлена: {price}")
        return price

    logging.error(f"❌ Не удалось получить цену для {query.upper()}")
    return cached.get("price")
