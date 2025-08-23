# config.py
# Единая точка чтения ENV с дефолтами, чтобы анализ работал «из коробки».

import os
from typing import Any

def getenv_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}

def getenv_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

def getenv_int(name: str, default: int) -> int:
    try:
        return int(float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default

# === Переключатели источников рынка/новостей ===
ENABLE_FNG: bool  = getenv_bool("ENABLE_FNG", True)     # учитывать Fear & Greed
ENABLE_NEWS: bool = getenv_bool("ENABLE_NEWS", True)    # учитывать новостной фон

# === Пороговые значения Fear & Greed ===
FNG_EXTREME_GREED: int = getenv_int("FNG_EXTREME_GREED", 75)
FNG_EXTREME_FEAR: int  = getenv_int("FNG_EXTREME_FEAR", 25)

# === Рынок/защита (market guard) ===
# если BTC за 24ч упал сильнее этого порога (в минус), сигналы отключаются
MARKET_GUARD_BTC_DROP: float = getenv_float("MARKET_GUARD_BTC_DROP", 3.0)  # %

# === Фильтры тренда и перегрева ===
NEGATIVE_TREND_7D_CUTOFF: float = getenv_float("NEGATIVE_TREND_7D_CUTOFF", -6.0)  # отбрасываем монеты со спадом 7д <= -6%
PUMP_CUTOFF_24H: float          = getenv_float("PUMP_CUTOFF_24H", 12.0)           # отбрасываем при перегреве за 24ч >= 12%

# === Ликвидность (суточный объём, USD) ===
MIN_LIQUIDITY_USD: float = getenv_float("MIN_LIQUIDITY_USD", 5_000_000.0)
MAX_LIQUIDITY_USD: float = getenv_float("MAX_LIQUIDITY_USD", 100_000_000.0)

# === Настройки новостей/кэша (используются sentiment_utils/crypto_utils при наличии ENV) ===
NEWS_TTL: int            = getenv_int("NEWS_TTL", 3600)        # кэш новостей, сек
NEWS_SCORE_CLAMP: float  = getenv_float("NEWS_SCORE_CLAMP", 0.6)
FNG_TTL: int             = getenv_int("FNG_TTL", 1800)         # кэш F&G, сек
HTTP_TIMEOUT: float      = getenv_float("HTTP_TIMEOUT", 20.0)
HTTP_MAX_RETRIES: int    = getenv_int("HTTP_MAX_RETRIES", 6)
HTTP_BACKOFF_BASE: float = getenv_float("HTTP_BACKOFF_BASE", 1.7)

# Опционально: токен CryptoPanic и/или собственный прокси новостей
CRYPTOPANIC_TOKEN: str   = os.getenv("CRYPTOPANIC_TOKEN", "")
NEWS_BASE: str           = os.getenv("NEWS_BASE", "")  # например, https://your-proxy.example
