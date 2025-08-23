# crypto_utils.py
# Аккуратные правки: anti‑429, единый aiohttp‑сеанс, кэш историй цен с TTL, атомарная запись кеша.
import aiohttp
import json
import os
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Any, Dict, List, Optional

CACHE_PATH = "indicators_cache.json"

# ---- Параметры, чтобы не ловить 429 (всё с дефолтами как у тебя, но настраиваемо через ENV)
CG_CHUNK_SIZE = int(os.getenv("CG_CHUNK_SIZE", "45"))          # размер чанка /coins/markets
CG_CHUNK_PAUSE = float(os.getenv("CG_CHUNK_PAUSE", "2"))       # сек пауза между чанками
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "6"))     # попыток на запрос
HTTP_BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "1.7"))
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))
HIST_TTL_MIN = int(os.getenv("HIST_TTL_MIN", "240"))           # TTL историй цен (минуты)
INDIC_TTL_MIN = int(os.getenv("INDIC_TTL_MIN", "30"))          # TTL RSI/MA/price (минуты)

# ---- Загрузка/сохранение кеша
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

# ---- Вспомогательные
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
    # Сохраняем твою логику: RSI по последним 8 точкам.
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

# ---- Единый aiohttp‑клиент
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
                headers={
                    "Accept": "application/json",
                    "User-Agent": "AnSamBot/anti429"
                }
            )
    return _SESSION

async def _request_json(method: str, url: str, *, params: Dict[str, Any] = None) -> Any:
    """
    Унифицированный запрос с уважением 429/Retry-After, экспоненциальным backoff и максимумом попыток.
    """
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
                            wait_s = min(5.0 * attempt, 30.0)
                    else:
                        wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 25.0)
                    logging.warning(f"⚠️ 429 по {url}. Ждём {round(wait_s,2)} сек (попытка {attempt})")
                    await asyncio.sleep(wait_s)
                    continue

                if 500 <= resp.status < 600:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"{resp.status} after {attempt} retries: {url}")
                    wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 20.0)
                    logging.warning(f"⚠️ {resp.status} по {url}. Повтор через {round(wait_s,2)} сек (попытка {attempt})")
                    await asyncio.sleep(wait_s)
                    continue

                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            attempt += 1
            if attempt > HTTP_MAX_RETRIES:
                raise
            wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.2 * attempt, 20.0)
            logging.warning(f"⚠️ Ошибка запроса {e}. Повтор через {round(wait_s,2)} сек (попытка {attempt})")
            await asyncio.sleep(wait_s)

# ---- Данные CoinGecko
async def fetch_historical_prices(coin_id, days=30):
    """
    Истории цен с кэшем. TTL задаётся HIST_TTL_MIN.
    Сохраняем в INDICATOR_CACHE[coin_id]['hist_prices'] и 'hist_ts'.
    """
    now = datetime.utcnow()
    node = INDICATOR_CACHE.get(coin_id, {})
    ts_str = node.get("hist_ts")
    if ts_str:
        try:
            ts = datetime.fromisoformat(ts_str)
            if now - ts < timedelta(minutes=HIST_TTL_MIN):
                prices_cached = node.get("hist_prices")
                if isinstance(prices_cached, list) and prices_cached:
                    return [safe_float(p) for p in prices_cached]
        except Exception:
            pass

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    try:
        data = await _request_json("GET", url, params=params)
        prices = [safe_float(price[1]) for price in data.get("prices", [])]
    except Exception:
        prices = []

    INDICATOR_CACHE.setdefault(coin_id, {})
    INDICATOR_CACHE[coin_id]["hist_prices"] = prices
    INDICATOR_CACHE[coin_id]["hist_ts"] = now.isoformat()
    save_cache()
    return prices

async def fetch_all_coin_data(coin_ids: List[str]):
    """Получает данные с CoinGecko чанками с защитой от 429. Формат — как раньше."""
    results = []
    if not coin_ids:
        return results

    url = "https://api.coingecko.com/api/v3/coins/markets"
    # Бэмпов не меняем: 24h и 7d как у тебя
    base_params = {
        "vs_currency": "usd",
        "price_change_percentage": "24h,7d"
    }

    for i in range(0, len(coin_ids), CG_CHUNK_SIZE):
        chunk = coin_ids[i:i + CG_CHUNK_SIZE]
        params = {**base_params, "ids": ",".join(chunk)}

        try:
            data = await _request_json("GET", url, params=params)
            if isinstance(data, list):
                results.extend(data)
            else:
                logging.error(f"❌ Непредвиденный формат ответа по чанку {chunk[:3]}... (len={len(chunk)})")
        except Exception as e:
            logging.error(f"❌ Ошибка API для монет {chunk[:3]}...: {e}")

        # Пауза между чанками (уважение к лимитам)
        await asyncio.sleep(CG_CHUNK_PAUSE)

    return results

async def get_all_coin_data(coin_ids):
    raw_data = await fetch_all_coin_data(coin_ids)
    received_ids = {coin.get("id") for coin in raw_data}
    result = []

    for coin in raw_data:
        coin_id = coin.get("id", "")
        current_price = safe_float(coin.get("current_price"))
        change_24h = safe_float(coin.get("price_change_percentage_24h"))
        change_7d = safe_float(coin.get("price_change_percentage_7d_in_currency"))
        volume = safe_float(coin.get("total_volume"))

        cached = INDICATOR_CACHE.get(coin_id, {})
        timestamp = cached.get("timestamp")
        now = datetime.utcnow()
        is_fresh = timestamp and (now - datetime.fromisoformat(timestamp)) < timedelta(minutes=INDIC_TTL_MIN)

        if is_fresh:
            rsi = safe_float(cached.get("rsi"))
            ma7 = safe_float(cached.get("ma7"))
            ma30 = safe_float(cached.get("ma30"))
        else:
            prices = await fetch_historical_prices(coin_id, days=30)
            # Твоя логика с фоллбэками — оставляем
            rsi = calculate_rsi(prices[-8:]) or simulate_rsi(change_24h)
            ma7 = calculate_ma(prices, days=7) or simulate_ma(current_price, days=7)
            ma30 = calculate_ma(prices, days=30) or simulate_ma(current_price, days=30)
            INDICATOR_CACHE[coin_id] = {
                **INDICATOR_CACHE.get(coin_id, {}),
                "rsi": rsi,
                "ma7": ma7,
                "ma30": ma30,
                "timestamp": now.isoformat(),
                "price": current_price
            }

        coin["current_price"] = current_price
        coin["price_change_percentage_24h"] = change_24h
        coin["price_change_percentage_7d"] = change_7d
        coin["total_volume"] = volume
        coin["rsi"] = rsi
        coin["ma7"] = ma7
        coin["ma30"] = ma30
        coin["no_data"] = False

        result.append(coin)

    # Добавляем заглушки для монет, которые не вернул API
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

    # 1. Проверка кеша (свежий — моложе 15 минут)
    cached = INDICATOR_CACHE.get(coin_id, {})
    timestamp = cached.get("timestamp")
    now = datetime.utcnow()
    if timestamp and (now - datetime.fromisoformat(timestamp)) < timedelta(minutes=15):
        if cached.get("price") is not None:
            logging.info(f"📌 Цена {query.upper()} взята из кеша: {cached['price']}")
            return cached["price"]

    # 2. Попробуем запросы (до 3 попыток)
    attempts = 0
    while attempts < 3:
        coins = await get_all_coin_data([coin_id])
        if coins and coins[0] and coins[0].get("current_price") is not None:
            price = coins[0].get("current_price")
            INDICATOR_CACHE.setdefault(coin_id, {})
            INDICATOR_CACHE[coin_id]["price"] = price
            INDICATOR_CACHE[coin_id]["timestamp"] = now.isoformat()
            save_cache()
            logging.info(f"📌 Цена для {query.upper()} обновлена: {price}")
            return price
        attempts += 1
        wait_time = 5 * attempts
        logging.warning(f"⚠️ Попытка {attempts} не удалась для {query.upper()}, повтор через {wait_time} сек")
        await asyncio.sleep(wait_time)

    logging.error(f"❌ Не удалось получить цену для {query.upper()} после 3 попыток")
    return cached.get("price")  # fallback: хотя бы кеш
