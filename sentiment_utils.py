# sentiment_utils.py
# Новости и Fear&Greed: сначала CryptoPanic (если есть токен), иначе RSS (безлимитно).
import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List, Tuple
import re
import aiohttp
import xml.etree.ElementTree as ET

CACHE_PATH = os.getenv("INDICATORS_CACHE_FILE", "indicators_cache.json")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "6"))
HTTP_BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "1.7"))

# Fear & Greed
FNG_API = os.getenv("FNG_API", "https://api.alternative.me/fng/")
FNG_TTL = int(os.getenv("FNG_TTL", "1800"))  # сек

# CryptoPanic (опционально)
CRYPTOPANIC_TOKEN = os.getenv("CRYPTOPANIC_TOKEN")

# RSS (бесплатно)
RSS_TTL = int(os.getenv("RSS_TTL", "900"))  # 15 минут кэш фидов
NEWS_TTL_DEFAULT = int(os.getenv("NEWS_TTL", "3600"))  # кэш итогового news_score по монете
NEWS_SCORE_CLAMP = float(os.getenv("NEWS_SCORE_CLAMP", "0.6"))

# Список RSS можно переопределить переменной окружения RSS_FEEDS="url1,url2,..."
DEFAULT_RSS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",               # CoinDesk
    "https://cointelegraph.com/rss",                                  # Cointelegraph
    "https://www.binance.com/en/support/announcement/c-48?navId=48&rss=true",  # Binance Announcements (en)
    "https://www.theblock.co/rss",                                    # The Block (если недоступен — будет тихий пропуск)
    "https://messari.io/rss",                                         # Messari (если включён)
]
RSS_FEEDS = [u.strip() for u in os.getenv("RSS_FEEDS", ",".join(DEFAULT_RSS)).split(",") if u.strip()]

# ------- Кэш -------
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

def _cache_get(ns: str, key: str, ttl_sec: int):
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

def _cache_set(ns: str, key: str, val: Any):
    CACHE.setdefault(ns, {})[key] = {"ts": datetime.utcnow().isoformat(), "val": val}
    _save_cache(CACHE)

# ------- HTTP -------
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
                headers={"Accept": "application/json, text/xml;q=0.9, */*;q=0.8", "User-Agent": "AnSamBot/news"}
            )
    return _SESSION

async def _request_json(method: str, url: str, params: Dict[str, Any] | None = None) -> Any:
    session = await _get_session()
    attempt = 0
    while True:
        try:
            async with session.request(method.upper(), url, params=params) as r:
                if r.status in (402, 403, 429):  # платёж/лимит/лимит — уходим на RSS
                    raise RuntimeError(f"HTTP {r.status}")
                if 500 <= r.status < 600:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"{r.status}")
                    await asyncio.sleep(min((HTTP_BACKOFF_BASE ** attempt) + 0.1*attempt, 20.0))
                    continue
                r.raise_for_status()
                return await r.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            attempt += 1
            if attempt > HTTP_MAX_RETRIES:
                raise
            await asyncio.sleep(min((HTTP_BACKOFF_BASE ** attempt) + 0.2*attempt, 20.0))

async def _request_text(url: str) -> str:
    session = await _get_session()
    attempt = 0
    while True:
        try:
            async with session.get(url) as r:
                if r.status in (402, 403, 429):
                    raise RuntimeError(f"HTTP {r.status}")
                if 500 <= r.status < 600:
                    attempt += 1
                    if attempt > HTTP_MAX_RETRIES:
                        raise RuntimeError(f"{r.status}")
                    await asyncio.sleep(min((HTTP_BACKOFF_BASE ** attempt) + 0.1*attempt, 20.0))
                    continue
                r.raise_for_status()
                return await r.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            attempt += 1
            if attempt > HTTP_MAX_RETRIES:
                raise
            await asyncio.sleep(min((HTTP_BACKOFF_BASE ** attempt) + 0.2*attempt, 20.0))

# ------- Fear & Greed -------
def _classify_fng(v: int) -> str:
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 54: return "Neutral"
    if v <= 74: return "Greed"
    return "Extreme Greed"

async def get_fear_greed() -> Dict[str, Any]:
    cached = _cache_get("fng", "data", FNG_TTL)
    if cached:
        return cached
    try:
        data = await _request_json("GET", FNG_API)
        row = (data.get("data") or [{}])[0]
        val = int(row.get("value") or 50)
        cls = row.get("value_classification") or _classify_fng(val)
        out = {"value": val, "classification": str(cls)}
    except Exception:
        out = {"value": 50, "classification": "Neutral"}
    _cache_set("fng", "data", out)
    return out

# ------- CryptoPanic (если доступен) -------
async def _news_via_cryptopanic(symbol: str) -> Optional[float]:
    if not CRYPTOPANIC_TOKEN:
        return None
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": CRYPTOPANIC_TOKEN,
        "currencies": symbol.upper(),
        "filter": "rising|hot|important|bullish|bearish|news",
        "kind": "news",
        "public": "true",
        "regions": "en"  # чтобы не мешался нерелевантный язык
    }
    try:
        data = await _request_json("GET", url, params=params)
        results = data.get("results") or []
    except Exception:
        return None

    if not results:
        return 0.0

    def _weight(ts: str) -> float:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hours = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)
            return max(0.2, 1.0 - hours / 72.0)
        except Exception:
            return 0.5

    score_sum = 0.0
    weight_sum = 0.0
    for item in results:
        votes = item.get("votes") or {}
        pos = float(votes.get("positive") or 0.0)
        neg = float(votes.get("negative") or 0.0)
        local = 0.0 if (pos + neg) == 0 else (pos - neg) / (pos + neg)
        w = _weight(item.get("published_at") or "")
        score_sum += local * w
        weight_sum += w

    return 0.0 if weight_sum == 0 else max(-1.0, min(1.0, score_sum / weight_sum))

# ------- RSS (бесплатный фоллбек) -------
_POS_WORDS = [
    "partnership","integration","listing","launch","upgrade","funding","raised",
    "approve","approved","mainnet","testnet","airdrop","reward","expansion","surge","growth","token burn"
]
_NEG_WORDS = [
    "hack","exploit","breach","lawsuit","ban","delist","halt","outage",
    "downtime","rug","scam","investigation","charge","fine","sanction","vulnerability"
]
_SYM_EXTRAS = {
    # при желании можно вручную дополнять: "AIXBT": ["ai xbt", "xbt ai"]
}

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()

def _pick_entries_from_rss(xml_text: str) -> List[Tuple[str,str,str]]:
    """Возвращает [(title, summary, published_iso), ...]"""
    out: List[Tuple[str,str,str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    # RSS 2.0
    for item in root.findall(".//item"):
        title = "".join(item.findtext("title") or "").strip()
        summary = "".join(item.findtext("description") or "").strip()
        pub = item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date") or ""
        out.append((title, summary, pub))
    # Atom
    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = "".join(entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        summary = "".join(entry.findtext("{http://www.w3.org/2005/Atom}summary") or entry.findtext("{http://www.w3.org/2005/Atom}content") or "").strip()
        pub = entry.findtext("{http://www.w3.org/2005/Atom}updated") or entry.findtext("{http://www.w3.org/2005/Atom}published") or ""
        out.append((title, summary, pub))
    return out

def _parse_rfc822_or_iso(dt_str: str) -> Optional[datetime]:
    try:
        # RFC-822: 'Sun, 11 Aug 2024 09:00:00 GMT'
        return datetime.strptime(dt_str[:31], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None

async def _fetch_all_rss() -> List[Tuple[str,str,str]]:
    cached = _cache_get("rss", "all", RSS_TTL)
    if cached:
        return cached
    entries: List[Tuple[str,str,str]] = []
    for url in RSS_FEEDS:
        try:
            text = await _request_text(url)
            entries.extend(_pick_entries_from_rss(text))
        except Exception:
            continue
    # храним только последние ~500 записей, чтобы не раздувать кеш
    entries = entries[-500:]
    _cache_set("rss", "all", entries)
    return entries

def _score_from_text(text: str) -> float:
    t = _normalize(text)
    pos = sum(1 for w in _POS_WORDS if w in t)
    neg = sum(1 for w in _NEG_WORDS if w in t)
    if pos == 0 and neg == 0:
        return 0.0
    return (pos - neg) / float(pos + neg)  # [-1..+1]

def _weight_by_recency(pub: Optional[datetime]) -> float:
    if not pub:
        return 0.5
    hours = max(0.0, (datetime.now(timezone.utc) - pub).total_seconds() / 3600.0)
    if hours <= 24: return 1.0
    if hours <= 48: return 0.6
    if hours <= 72: return 0.3
    return 0.0

async def _news_via_rss(symbol: str) -> float:
    entries = await _fetch_all_rss()
    sym = symbol.upper()
    keys = {sym, sym.lower()}
    # добавим id из crypto_list, если доступен
    try:
        from crypto_list import TELEGRAM_WALLET_COIN_IDS
        # найти id по символу
        for cid, s in TELEGRAM_WALLET_COIN_IDS.items():
            if s.upper() == sym:
                keys.add(cid.lower())
                keys.add(cid.replace("-", " ").lower())
                break
    except Exception:
        pass
    # вручную заданные расширения
    for extra in _SYM_EXTRAS.get(sym, []):
        keys.add(extra.lower())

    score_sum = 0.0
    weight_sum = 0.0
    for title, summary, pub in entries:
        blob = f"{title} {summary}"
        blob_n = _normalize(blob)
        if not any(k in blob_n for k in keys):
            continue
        w = _weight_by_recency(_parse_rfc822_or_iso(pub))
        if w <= 0:
            continue
        local = _score_from_text(title) * 0.7 + _score_from_text(summary) * 0.3
        score_sum += local * w
        weight_sum += w

    if weight_sum == 0:
        return 0.0
    return max(-1.0, min(1.0, score_sum / weight_sum))

# ------- Публичные функции, используемые в analysis.py -------
async def get_news_sentiment(symbol: str, ttl: int = NEWS_TTL_DEFAULT) -> float:
    """Возвращает тональность [-1..+1], сжимает амплитуду NEWS_SCORE_CLAMP, кэширует на ttl."""
    key = symbol.upper()
    cached = _cache_get("news_sentiment", key, ttl)
    if cached is not None:
        return float(cached)

    tone: Optional[float] = None
    # 1) пробуем CryptoPanic (если есть токен)
    if CRYPTOPANIC_TOKEN:
        tone = await _news_via_cryptopanic(key)

    # 2) если не получилось/лимит/нет токена — RSS
    if tone is None:
        tone = await _news_via_rss(key)

    tone = max(-1.0, min(1.0, float(tone))) * NEWS_SCORE_CLAMP
    _cache_set("news_sentiment", key, tone)
    return tone
