import json
import os

CACHE_FILE = "top3_cache.json"

def save_top3(top3_list):
    with open(CACHE_FILE, "w") as f:
        json.dump(top3_list, f)

def get_top3():
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []
