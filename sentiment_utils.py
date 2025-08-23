# sentiment_utils.py
# Ассинхронные утилиты новостей и Fear&Greed с кэшем и анти‑429.
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp

CACHE_PATH = os.getenv("INDICATORS_CACHE_FILE", "indicators_cache.json")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "6"))
HTTP_BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "1.7"))

# ---- Fear&Greed
FNG_API = os.getenv("FNG_API", "https://api.alternative.me/fng/")  # публичный эндпоинт
FNG_TTL = int(os.getenv("FNG_TTL", "1800"))  # 30 минут

# ---- Новости
# Вариант 1: свой прокси (должен вернуть {"tone": -1..+1})
NEWS_BASE = os.getenv("NEWS_BASE")  # например, https://your-proxy.example
# Вариант 2: CryptoPanic (рекомендуется)
CRYPTOPANIC_TOKEN = os.getenv("CRYPTOPANIC_TOKEN")
NEWS_TTL_DEFAULT = int(os.getenv("NEWS_TTL", "3600"))  # 60 минут
NEWS_SCORE_CLAMP = float(os.getenv("NEWS_SCORE_CLAMP", "0.6"))  # итоговый |score| <= 0.6

# ---- Кэш
def _load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache: Dict[str, Any]) -> None:
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_PATH)

CACHE = _load_cache()

def _cache_get(ns: str, key: str, ttl_sec: int) -> Optional[Any]:
    node = CACHE.get(ns, {}).get(key)
    if not node:
        return None
    try:
        ts = datetime.fromisoformat(node["ts"])
    except Exception:
        return None
    if datetime.utcnow() - ts > timedelta(seconds=ttl_sec):
        return None
    return node["val"]

def _cache_set(ns: str, key: str, val: Any) -> None:
    CACHE.setdefault(ns, {})[key] = {"ts": datetime.utcnow().isoformat(), "val": val}
    _save_cache(CACHE)

# ---- HTTP
_SESSION: Optional[aiohttp.ClientSession] = None
_LOCK = asyncio.Lock()

async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION and not _SESSION.closed:
        return _SESSION
    async with _LOCK:
        if _SESSION is None or _SESSION.closed:
            timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            _SESSION = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Accept": "application/json", "User-Agent": "AnSamBot/sentiment-anti429"}
            )
    return _SESSION

async def _request_json(method: str, url: str, params: Dict[str, Any] | None = None) -> Any:
    session = await _get_session()
    attempt = 0
    while True:
        try:
            async with session.request(method.upper(), url, params=params) as r:
                if r.status == 429:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"News/FNG 429 after {attempt} retries: {url}")
                    retry_after = r.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_s = min(float(retry_after), 30.0)
                        except ValueError:
                            wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 25.0)
                    else:
                        wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 25.0)
                    await asyncio.sleep(wait_s)
                    continue
                if 500 <= r.status < 600:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"News/FNG {r.status} after {attempt} retries: {url}")
                    wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.1 * attempt, 20.0)
                    await asyncio.sleep(wait_s)
                    continue
                r.raise_for_status()
                return await r.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            attempt += 1
            if attempt > HTTP_MAX_RETRIES:
                raise
            wait_s = min((HTTP_BACKOFF_BASE ** attempt) + 0.2 * attempt, 20.0)
            await asyncio.sleep(wait_s)

# ---- Fear & Greed
def _classify_fng(v: int) -> str:
    if v <= 24:
        return "Extreme Fear"
    if v <= 44:
        return "Fear"
    if v <= 54:
        return "Neutral"
    if v <= 74:
        return "Greed"
    return "Extreme Greed"

async def get_fear_greed() -> Dict[str, Any]:
    cached = _cache_get("fng", "data", FNG_TTL)
    if cached:
        return cached
    try:
        data = await _request_json("GET", FNG_API)
        # формат alternative.me: {"data":[{"value":"60","value_classification":"Greed", ...}]}
        row = (data.get("data") or [{}])[0]
        val = int(row.get("value") or 50)
        cls = row.get("value_classification") or _classify_fng(val)
        out = {"value": val, "classification": str(cls)}
    except Exception:
        # нейтрально, если API не доступен
        out = {"value": 50, "classification": "Neutral"}
    _cache_set("fng", "data", out)
    return out

# ---- Новости / тональность [-1..+1]
async def _news_via_proxy(symbol: str) -> float:
    """Ожидаем от прокси JSON {"tone": -1..+1} по параметру symbol."""
    url = f"{NEWS_BASE.rstrip('/')}/v1/news"
    params = {"symbol": symbol.upper()}
    try:
        data = await _request_json("GET", url, params=params)
        tone = float(data.get("tone", 0.0))
        return max(-1.0, min(1.0, tone))
    except Exception:
        return 0.0

async def _news_via_cryptopanic(symbol: str) -> float:
    """
    Берём ленту новостей по монете и агрегируем: (positive - negative) / (positive + negative),
    с убывающим весом на сроке до 72 часов.
    """
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "currencies": symbol.upper(),
        "filter": "rising|hot|important|bullish|bearish|news",  # расширяем
        "kind": "news",
        "public": "true"
    }
    try:
        data = await _request_json("GET", url, params=params)
        results = data.get("results") or []
    except Exception:
        results = []

    if not results:
        return 0.0

    def _weight(published_at: str) -> float:
        try:
            # 2025-08-23T15:47:02Z
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            hours = max(0.0, (datetime.utcnow() - dt.replace(tzinfo=None)).total_seconds() / 3600.0)
            # последние 24ч — вес ~1, к 72ч падает до 0.2
            return max(0.2, 1.0 - hours / 72.0)
        except Exception:
            return 0.5

    score_sum = 0.0
    weight_sum = 0.0
    for item in results:
        votes = item.get("votes") or {}
        pos = float(votes.get("positive") or 0.0)
        neg = float(votes.get("negative") or 0.0)
        denom = pos + neg
        local = 0.0 if denom == 0 else (pos - neg) / denom  # [-1..+1]
        w = _weight(item.get("published_at") or "")
        score_sum += local * w
        weight_sum += w

    if weight_sum <= 0:
        return 0.0
    tone = max(-1.0, min(1.0, score_sum / weight_sum))
    return tone

async def get_news_sentiment(symbol: str, ttl: int = NEWS_TTL_DEFAULT) -> float:
    """
    Возвращает тональность [-1..+1], затем мягко «срезает» амплитуду NEWS_SCORE_CLAMP.
    Кэшируется на ttl секунд по ключу монеты.
    """
    key = symbol.upper()
    cached = _cache_get("news_sentiment", key, ttl)
    if cached is not None:
        return float(cached)

    if NEWS_BASE:
        tone = await _news_via_proxy(key)
    elif CRYPTOPANIC_TOKEN:
        tone = await _news_via_cryptopanic(key)
    else:
        # нет источника — нейтрально
        tone = 0.0

    tone = max(-1.0, min(1.0, tone)) * NEWS_SCORE_CLAMP
    _cache_set("news_sentiment", key, tone)
    return tone
