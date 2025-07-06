from typing import Dict, List
from core.analyzer import analyze_coin
from data.crypto_list import CRYPTO_LIST
from utils.formatter import format_signal

async def generate_daily_signal() -> Dict:
    analyzed_coins = []
    
    for coin in CRYPTO_LIST:
        analysis = analyze_coin(coin["id"])
        if not analysis:
            continue
            
        analyzed_coins.append({
            "id": coin["id"],
            "symbol": coin["symbol"],
            "price": analysis.get("current_price"),
            "rsi": analysis["rsi"],
            "ma7": analysis["ma7"],
            "ma20": analysis["ma20"],
            "trend": analysis["trend"]
        })
    
    # Фильтрация: RSI < 70, восходящий тренд
    filtered = [
        c for c in analyzed_coins 
        if c["rsi"] and c["rsi"] < 70 
        and c["trend"] == "up"
    ]
    
    # Сортировка по RSI (ниже = лучше)
    best_coins = sorted(filtered, key=lambda x: x["rsi"])[:3]
    
    return {
        "top_1": format_signal(best_coins[0]),
        "top_3": [format_signal(coin) for coin in best_coins]
    }
