import aiohttp
import asyncio
from typing import Optional

COINGECKO_API = "https://api.coingecko.com/api/v3"

class CoinGeckoClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()
    
    async def get_price(self, coin_id: str) -> Optional[float]:
        try:
            url = f"{COINGECKO_API}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}
            
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
                return data[coin_id]["usd"]
                
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None
