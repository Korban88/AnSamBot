import aiohttp
import asyncio
import time
from typing import Optional, Dict, Any
import logging

from config import CRYPTOPANIC_TOKEN

logger = logging.getLogger(__name__)

# простые кэши, чтобы не спамить API
_FNG_CACHE = {"ts": 0.0, "data": None}
_NEWS_CACHE: Dict[str, Dict[str, Any]] = {}  # key -> {"ts": float, "score": float}

# глобальный кулдаун для CryptoPanic (после 429 не ходим N минут)
_NEWS_COOLDOWN_UNTIL: float = 0.0

FNG_URL = "https://api.alternative.me/fng/"          # Fear & Greed Index (без ключа)
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"

def _now() -> float:
    return time.time()

async def _retryable_get(session: aiohttp.ClientSession, url: str, **kwargs):
    """Универсальный ретраер для GET: 200 — вернём сразу, 429/5xx — пара бэкоффов."""
    backoffs = [6, 12, 18]
    for i in range(3):
        r = await session.get(url, **kwargs)
        if r.status == 200:
            return r
        if r.status in (429, 500, 502, 503, 504) and i < 2:
            wait = backoffs[i]
            logger.warning(f"HTTP {r.status} → повтор через {wait} сек")
            await asyncio.sleep(wait)
            continue
        return r  # вернём последний ответ (может быть 429/5xx)

async def get_fear_greed(ttl: int = 1800) -> Optional[Dict[str, Any]]:
    """
    Возвращает dict: {"value": int 0..100, "classification": str}
    Кэш: 30 минут по умолчанию.
    """
    now = _now()
    if _FNG_CACHE["data"] and (now - _FNG_CACHE["ts"] < ttl):
        return _FNG_CACHE["data"]

    async with aiohttp.ClientSession() as s:
        r = await _retryable_get(s, FNG_URL, timeout=15)
        if not r or r.status != 200:
            logger.warning(f"F&G HTTP {getattr(r, 'status', None)}")
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

async def get_news_sentiment(query: str, ttl: int = 1800, limit: int = 25) -> Optional[float]:
    """
    Агрегированный новостной скор от -1 до +1 (приблизительно), на базе CryptoPanic.
    query — обычно символ монеты (BTC/ETH/APE и т.п.) или coingecko id, что есть.
    Возвращает None, если токена нет / нет новостей / активен кулдаун после 429.
    """
    global _NEWS_COOLDOWN_UNTIL

    key = (query or "").strip().lower()
    if not key:
        return None

    now = _now()

    # глобальный кулдаун после 429: до this_time не ходим за новостями вовсе
    if now < _NEWS_COOLDOWN_UNTIL:
        return None

    if key in _NEWS_CACHE and (now - _NEWS_CACHE[key]["ts"] < ttl):
        return _NEWS_CACHE[key]["score"]

    if not CRYPTOPANIC_TOKEN:
        # модуль включён, но токена нет — просто не используем новости
        return None

    params_tick = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "currencies": query.upper(),   # CryptoPanic понимает tickers/aliases
        "filter": "hot",
        "kind": "news"
    }
    params_text = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "q": query,
        "filter": "hot",
        "kind": "news"
    }

    score = 0
    cnt = 0
    try:
        async with aiohttp.ClientSession() as s:
            # Сначала пробуем по тикеру
            r = await _retryable_get(s, CRYPTOPANIC_URL, params=params_tick, timeout=15)
            if not r or r.status != 200:
                if r and r.status == 429:
                    _NEWS_COOLDOWN_UNTIL = now + 10 * 60  # 10 минут кулдаун
                    logger.warning("CryptoPanic rate-limited → включен 10‑минутный кулдаун")
                else:
                    logger.warning(f"CryptoPanic HTTP {getattr(r, 'status', None)} for {query}")
                return None

            j = await r.json()
            results = j.get("results", [])[:limit]

            # если по тикеру пусто — пробуем текстовый поиск
            if not results:
                r2 = await _retryable_get(s, CRYPTOPANIC_URL, params=params_text, timeout=15)
                if r2 and r2.status == 200:
                    j2 = await r2.json()
                    results = j2.get("results", [])[:limit]
                elif r2 and r2.status == 429:
                    _NEWS_COOLDOWN_UNTIL = now + 10 * 60
                    logger.warning("CryptoPanic rate-limited (q-search) → включен 10‑минутный кулдаун")
                    return None

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
