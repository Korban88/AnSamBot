import os

def reset_cache():
    files = [
        "indicators_cache.json",
        "used_symbols.json"
    ]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
