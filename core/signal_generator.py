import asyncio
from typing import Dict, List, Optional
from utils.api_client import CoinGeckoClient
from utils.formatter import format_signal
from data.crypto_list import CRYPTO_LIST
import logging

logger = logging.getLogger(__name__)
client = CoinGeckoClient()

async def get_coin_analysis(coin_id: str) -> Optional[Dict]:
    """Получает и анализирует данные одной монеты"""
    try:
        data = await client.get_coin_data(coin_id)
        if not data:
            return None

        market_data = data.get('market_data', {})
        return {
            'id': coin_id,
            'symbol': data.get('symbol', '').upper(),
            'price': market_data.get('current_price', {}).get('usd', 0),
            'change_24h': market_data.get('price_change_percentage_24h', 0),
            'rsi': None,  # Будет рассчитано отдельно
            'ma7': None,
            'ma20': None
        }
    except Exception as e:
        logger.error(f"Ошибка анализа {coin_id}: {str(e)}")
        return None

async def generate_top_signals() -> Dict:
    """Генерирует топ-3 сигнала"""
    tasks = [get_coin_analysis(coin['id']) for coin in CRYPTO_LIST]
    results = await asyncio.gather(*tasks)
    
    valid_coins = [coin for coin in results if coin is not None]
    
    # Фильтрация и сортировка
    filtered = sorted(
        [c for c in valid_coins if c['change_24h'] > -3],  # Исключаем падающие
        key=lambda x: x['change_24h'],
        reverse=True
    )[:3]  # Топ-3 по росту

    return {
        'top_1': format_signal(filtered[0]) if len(filtered) > 0 else "Нет данных",
        'top_3': [format_signal(c) for c in filtered]
    }
