import os

def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")

# === Telegram ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c")
OWNER_ID = int(os.getenv("OWNER_ID", "347552741"))

# === Timezone / расписание ===
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
MORNING_SIGNAL_HOUR = int(os.getenv("MORNING_SIGNAL_HOUR", "8"))
EVENING_REPORT_HOUR = int(os.getenv("EVENING_REPORT_HOUR", "20"))

# === Переключатели модулей анализа ===
ENABLE_FNG = env_bool("ENABLE_FNG", True)       # Fear & Greed guard
ENABLE_NEWS = env_bool("ENABLE_NEWS", False)    # новостной фон (включай после установки токена)
ENABLE_FUNDING = env_bool("ENABLE_FUNDING", False)  # деривативы (на будущее)

# === Токены внешних сервисов (забираем из env) ===
CRYPTOPANIC_TOKEN = os.getenv("CRYPTOPANIC_TOKEN", "")   # для новостного фона
LUNARCRUSH_TOKEN = os.getenv("LUNARCRUSH_TOKEN", "")     # опционально
COINGLASS_TOKEN = os.getenv("COINGLASS_TOKEN", "")       # опционально

# === Издержки сделки ===
FEE_PER_TRADE_USD = float(os.getenv("FEE_PER_TRADE_USD", "1.0"))  # комиссия за одно действие (buy/sell)
SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "20"))               # проскальзывание в bps (20 = 0.20%)

# === Пороговые значения риск‑менеджмента ===
MARKET_GUARD_BTC_DROP = float(os.getenv("MARKET_GUARD_BTC_DROP", "-2.0"))  # если BTC < -2% за 24ч — глушим сигналы
FNG_EXTREME_GREED = int(os.getenv("FNG_EXTREME_GREED", "80"))
FNG_EXTREME_FEAR  = int(os.getenv("FNG_EXTREME_FEAR", "20"))

# === Ликвидность и тренды ===
MIN_LIQUIDITY_USD = int(os.getenv("MIN_LIQUIDITY_USD", "7000000"))
MAX_LIQUIDITY_USD = int(os.getenv("MAX_LIQUIDITY_USD", "150000000"))
PUMP_CUTOFF_24H = float(os.getenv("PUMP_CUTOFF_24H", "12.0"))           # выше — считаем перегревом
NEGATIVE_TREND_7D_CUTOFF = float(os.getenv("NEGATIVE_TREND_7D_CUTOFF", "-5.0"))  # ниже — жёсткий отсев
