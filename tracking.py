import asyncio
import logging
from crypto_utils import get_current_price
from config import TELEGRAM_ID
from aiogram import Bot

logger = logging.getLogger(__name__)

class CoinTracker:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.tracked = {}

    def track_coin(self, coin: str, price: float):
        self.tracked[coin] = {"start_price": price, "start_time": asyncio.get_event_loop().time()}

    async def _loop(self):
        while True:
            for coin, info in list(self.tracked.items()):
                current_price = await get_current_price(coin)
                if not current_price:
                    continue

                start_price = info["start_price"]
                percent_change = (current_price - start_price) / start_price * 100

                if percent_change >= 5:
                    await self.bot.send_message(TELEGRAM_ID, f"{coin.upper()} достигла цели +5%!")
                    del self.tracked[coin]
                elif percent_change >= 3.5 and not info.get("notified"):
                    await self.bot.send_message(TELEGRAM_ID, f"{coin.upper()} выросла на +3.5%")
                    self.tracked[coin]["notified"] = True
                elif asyncio.get_event_loop().time() - info["start_time"] > 43200:  # 12 часов
                    await self.bot.send_message(TELEGRAM_ID, f"{coin.upper()}: прошло 12ч, изменение: {percent_change:.2f}%")
                    del self.tracked[coin]

            await asyncio.sleep(600)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._loop())
