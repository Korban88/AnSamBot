import numpy as np
from typing import Dict, Optional
from crypto_utils import get_historical_prices

def calculate_rsi(prices: list, period: int = 14) -> Optional[float]:
    deltas = np.diff(prices)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    
    if len(losses) == 0:
        return 100.0
    
    avg_gain = np.mean(gains[-period:]) if len(gains) >= period else None
    avg_loss = np.mean(losses[-period:]) if len(losses) >= period else None
    
    if avg_gain is None or avg_loss is None:
        return None
        
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze_coin(coin_id: str) -> Dict[str, float]:
    prices = get_historical_prices(coin_id)
    if not prices or len(prices) < 20:
        return {}
    
    rsi = calculate_rsi(prices)
    ma7 = np.mean(prices[-7:])
    ma20 = np.mean(prices[-20:])
    
    return {
        "rsi": round(rsi, 2) if rsi else None,
        "ma7": round(ma7, 4),
        "ma20": round(ma20, 4),
        "trend": "up" if ma7 > ma20 else "down"
    }
