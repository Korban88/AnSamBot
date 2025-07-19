import os
import json

INDICATORS_CACHE_FILE = "indicators_cache.json"
SIGNALS_CACHE_FILE = "signals_cache.json"
LAST_SIGNALS_FILE = "last_signals.json"

def reset_cache():
    # Очистка indicators_cache.json
    if os.path.exists(INDICATORS_CACHE_FILE):
        with open(INDICATORS_CACHE_FILE, "w") as f:
            json.dump({}, f)

    # Очистка signals_cache.json
    if os.path.exists(SIGNALS_CACHE_FILE):
        with open(SIGNALS_CACHE_FILE, "w") as f:
            json.dump({}, f)

    # Очистка last_signals.json
    if os.path.exists(LAST_SIGNALS_FILE):
        with open(LAST_SIGNALS_FILE, "w") as f:
            json.dump([], f)

    return "Кэш успешно сброшен."
