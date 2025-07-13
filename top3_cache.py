import json
import os

CACHE_FILE = "top3_cache.json"

def get_top3():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_top3(top3_list):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(top3_list, file, ensure_ascii=False)
