import aiohttp
from config import config

async def fetch_coin_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    headers = {"x-cg-api-key": config.COINGECKO_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            return {
                'price': data['market_data']['current_price']['usd'],
                'rsi': data['market_data']['rsi_14'],
                'ma200': data['market_data']['moving_averages']['ma_200'],
                '24h_change': data['market_data']['price_change_percentage_24h']
            }
