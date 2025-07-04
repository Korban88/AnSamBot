import asyncio
import logging
from crypto_utils import get_price
from datetime import datetime

logger = logging.getLogger(__name__)

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}

    async def add(self, symbol):
        self.tracked[symbol] = {
            "start_time": datetime.utcnow(),
            "start_price": await get_price(symbol)
        }

    async def clear(self):
        self.tracked = {}

    async def run(self):
        to_remove = []
        for symbol, data in self.tracked.items():
            current_price = await get_price(symbol)
            if not current_price:
                continue

            start_price = data["start_price"]
            percent_change = ((current_price - start_price) / start_price) * 100
            time_passed = (datetime.utcnow() - data["start_time"]).total_seconds() / 3600

            if percent_change >= 5:
                await self.bot.send_message(
                    self.user_id,
                    f"🚀 *{symbol.upper()} вырос на +{percent_change:.2f}%!* Цель достигнута.",
                    parse_mode="Markdown"
                )
                to_remove.append(symbol)

            elif percent_change >= 3.5:
                await self.bot.send_message(
                    self.user_id,
                    f"📈 *{symbol.upper()} приближается к цели* (+{percent_change:.2f}%)",
                    parse_mode="Markdown"
                )

            elif time_passed >= 12:
                await self.bot.send_message(
                    self.user_id,
                    f"⏳ С момента отслеживания {symbol.upper()} прошло 12 часов. "
                    f"Изменение: {percent_change:.2f}%",
                    parse_mode="Markdown"
                )
                to_remove.append(symbol)

        for symbol in to_remove:
            self.tracked.pop(symbol, None)
