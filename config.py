# config.py
# Конфиг с правильными именами, чтобы main.py и utils.py не падали.

import os

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

# === Базовые параметры бота ===
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
OWNER_ID: int           = getenv_int("OWNER_ID", 347552741)  # твой Telegram ID (админ)

# === Переключатели анализа ===
ENABLE_FNG: bool  = getenv_bool("ENABLE_FNG", True)
ENABLE_NEWS: bool = getenv_bool("ENABLE_NEWS", True)

# === Пороговые значения Fear & Greed ===
FNG_EXTREME_GREED: int = getenv_int("FNG_EXTREME_GREED", 75)
FNG_EXTREME_FEAR: int  = getenv_int("FNG_EXTREME_FEAR", 25)

# === Рынок/защита (market guard) ===
MARKET_GUARD_BTC_DROP: float = getenv_float("MARKET_GUARD_BTC_DROP", 3.0)

# === Фильтры тренда и перегрева ===
NEGATIVE_TREND_7D_CUTOFF: float = getenv_float("NEGATIVE_TREND_7D_CUTOFF", -6.0)
PUMP_CUTOFF_24H: float          = getenv_float("PUMP_CUTOFF_24H", 12.0)

# === Ликвидность (суточный объём, USD) ===
MIN_LIQUIDITY_USD: float = getenv_float("MIN_LIQUIDITY_USD", 5_000_000.0)
MAX_LIQUIDITY_USD: float = getenv_float("MAX_LIQUIDITY_USD", 100_000_000.0)

# === Настройки новостей/кэша ===
NEWS_TTL: int            = getenv_int("NEWS_TTL", 3600)
NEWS_SCORE_CLAMP: float  = getenv_float("NEWS_SCORE_CLAMP", 0.6)
FNG_TTL: int             = getenv_int("FNG_TTL", 1800)
HTTP_TIMEOUT: float      = getenv_float("HTTP_TIMEOUT", 20.0)
HTTP_MAX_RETRIES: int    = getenv_int("HTTP_MAX_RETRIES", 6)
HTTP_BACKOFF_BASE: float = getenv_float("HTTP_BACKOFF_BASE", 1.7)

# Опционально
CRYPTOPANIC_TOKEN: str   = os.getenv("CRYPTOPANIC_TOKEN", "")
NEWS_BASE: str           = os.getenv("NEWS_BASE", "")
