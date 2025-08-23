import aiohttp
import time
from typing import Optional, Dict, Any
import logging

from config import CRYPTOPANIC_TOKEN

logger = logging.getLogger(__name__)

# простые кэши, чтобы не спамить API
_FNG_CACHE = {"ts": 0.0, "data": None}
_NEWS_CACHE: Dict[str, Dict[str, Any]] = {}  # key -> {"ts": float, "score": float}

FNG_URL = "https://api.alternative.me/fng/"          # Fear & Greed Index (без ключа)
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"

def _now() -> float:
    return time.time()

async def get_fear_greed(ttl: int = 1800) -> Optional[Dict[str, Any]]:
    """
    Возвращает dict: {"value": int 0..100, "classification": str}
    Кэш: 30 минут по умолчанию.
    """
    now = _now()
    if _FNG_CACHE["data"] and (now - _FNG_CACHE["ts"] < ttl):
        return _FNG_CACHE["data"]

    async with aiohttp.ClientSession() as s:
        async with s.get(FNG_URL, timeout=15) as r:
            if r.status != 200:
                logger.warning(f"F&G HTTP {r.status}")
                return None
            j = await r.json()
    try:
        item = j["data"][0]
        data = {"value": int(item["value"]), "classification": item.get("value_classification", "")}
        _FNG_CACHE["data"] = data
        _FNG_CACHE["ts"] = now
        return data
    except Exception as e:
        logger.warning(f"F&G parse error: {e}")
        return None


# очень лёгкий словарный сентимент по заголовку
_POS_HINTS = ("surge", "rally", "partnership", "integration", "listing", "mainnet", "raises", "sec approves",
              "etf ok", "funding", "upgrade", "launch", "support", "adds", "deploy")
_NEG_HINTS = ("hack", "exploit", "delist", "lawsuit", "sec sues", "halt", "outage", "rug", "ban",
              "sanction", "downgrade", "bug", "leak", "attack")

def _polarity(title: str) -> int:
    t = (title or "").lower()
    pos = any(w in t for w in _POS_HINTS)
    neg = any(w in t for w in _NEG_HINTS)
    return (1 if pos else 0) + (-1 if neg else 0)

async def get_news_sentiment(query: str, ttl: int = 1800, limit: int = 30) -> Optional[float]:
    """
    Агрегированный новостной скор от -1 до +1 (приблизительно), на базе CryptoPanic.
    query — обычно символ монеты (BTC/ETH/APE и т.п.) или coingecko id, что есть.
    Возвращает None, если CRYPTOPANIC_TOKEN не задан или нет новостей.
    """
    key = (query or "").strip().lower()
    if not key:
        return None

    now = _now()
    if key in _NEWS_CACHE and (now - _NEWS_CACHE[key]["ts"] < ttl):
        return _NEWS_CACHE[key]["score"]

    if not CRYPTOPANIC_TOKEN:
        # модуль включён, но токена нет — просто не используем новости
        return None

    params = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "currencies": query.upper(),   # CryptoPanic понимает tickers/aliases
        "filter": "hot",               # берём горячие/релевантные
        "kind": "news"
    }

    score = 0
    cnt = 0
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(CRYPTOPANIC_URL, params=params, timeout=15) as r:
                if r.status != 200:
                    logger.warning(f"CryptoPanic HTTP {r.status} for {query}")
                    return None
                j = await r.json()
                results = j.get("results", [])[:limit]
                for p in results:
                    title = p.get("title", "")
                    score += _polarity(title)
                    cnt += 1
    except Exception as e:
        logger.warning(f"CryptoPanic error for {query}: {e}")
        return None

    if cnt == 0:
        return None

    # нормируем примерно к [-1..+1]
    val = max(-1.0, min(1.0, score / max(cnt, 1)))
    _NEWS_CACHE[key] = {"ts": now, "score": val}
    return val
