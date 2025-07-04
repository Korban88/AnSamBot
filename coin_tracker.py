import asyncio
import logging
from crypto_utils import get_price_by_symbol

logger = logging.getLogger(__name__)


class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}  # {symbol: {'start_price': ..., 'start_time': ...}}

    async def add(self, symbol):
        current_price = get_price_by_symbol(symbol)
        if not current_price:
            return
        self.tracked[symbol] = {
            "start_price": current_price,
            "start_time": asyncio.get_event_loop().time()
        }

    async def clear(self):
        self.tracked.clear()

    async def run(self):
        for symbol, data in list(self.tracked.items()):
            current_price = get_price_by_symbol(symbol)
            if not current_price:
                continue

            change_percent = (current_price - data["start_price"]) / data["start_price"] * 100
            elapsed_time = asyncio.get_event_loop().time() - data["start_time"]

            if change_percent >= 5:
                await self.bot.send_message(
                    self.user_id,
                    f"🚀 {symbol.upper()} вырос на +5% с момента отслеживания!\nЦена: {current_price}"
                )
                del self.tracked[symbol]
            elif elapsed_time > 12 * 60 * 60:  # 12 часов
                await self.bot.send_message(
                    self.user_id,
                    f"⏱ По {symbol.upper()} прошло 12 часов. Изменение: {round(change_percent, 2)}%\nТекущая цена: {current_price}"
                )
                del self.tracked[symbol]
            elif change_percent >= 3.5:
                await self.bot.send_message(
                    self.user_id,
                    f"📈 {symbol.upper()} приближается к цели: +{round(change_percent, 2)}%\nЦена: {current_price}"
                )
