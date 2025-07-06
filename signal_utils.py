import json
from analysis import analyze_cryptos

SIGNAL_CACHE_FILE = "signal_cache.json"
INDEX_FILE = "signal_index.json"

def load_cached_signals():
    try:
        with open(SIGNAL_CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_cached_signals(signals):
    with open(SIGNAL_CACHE_FILE, "w") as f:
        json.dump(signals, f)

def load_signal_index():
    try:
        with open(INDEX_FILE, "r") as f:
            return json.load(f).get("index", 0)
    except FileNotFoundError:
        return 0

def save_signal_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump({"index": index}, f)

def reset_signal_index():
    save_signal_index(0)

async def get_next_signal_message():
    signals = load_cached_signals()
    index = load_signal_index()

    if not signals:
        signals = await analyze_cryptos()
        save_cached_signals(signals)
        index = 0

    if index >= len(signals):
        return None, None

    signal = signals[index]
    save_signal_index(index + 1)
    return signal["message"], signal["coin_id"]
