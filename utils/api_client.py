import aiohttp
import asyncio
from typing import Optional, Dict, Any
import json

COINGECKO_API = "https://api.coingecko.com/api/v3"

class CoinGeckoClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()
    
    async def _make_request(self, url: str, params: dict) -> Optional[Dict[str, Any]]:
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"CoinGecko API Error: {error}")
                    return None
                return await resp.json()
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
    
    async def get_price(self, coin_id: str) -> Optional[float]:
        params = {"ids": coin_id, "vs_currencies": "usd"}
        data = await self._make_request(
            f"{COINGECKO_API}/simple/price",
            params
        )
        return data.get(coin_id, {}).get("usd") if data else None
    
    async def get_coin_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        return await self._make_request(
            f"{COINGECKO_API}/coins/{coin_id}",
            params
        )
