import asyncio
import logging
from crypto_utils import get_current_price

logger = logging.getLogger(__name__)

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}

    async def add(self, symbol):
        price = get_current_price(symbol)
        if price is not None:
            self.tracked[symbol] = {
                "start_price": price,
                "start_time": asyncio.get_event_loop().time()
            }
            logger.info(f"▶️ Начато отслеживание {symbol} по цене {price}")
        else:
            logger.warning(f"❌ Не удалось получить цену для {symbol}")

    async def clear(self):
        self.tracked.clear()
        logger.info("🛑 Отслеживания очищены")

    async def run(self):
        to_remove = []
        for symbol, data in self.tracked.items():
            current_price = get_current_price(symbol)
            if current_price is None:
                continue

            start_price = data["start_price"]
            elapsed = asyncio.get_event_loop().time() - data["start_time"]
            change_percent = ((current_price - start_price) / start_price) * 100

            if change_percent >= 5:
                await self.bot.send_message(
                    self.user_id,
                    f"🎉 {symbol.upper()} вырос на +5% с момента отслеживания!\nТекущая цена: {current_price}",
                )
                to_remove.append(symbol)
            elif elapsed >= 12 * 60 * 60:
                await self.bot.send_message(
                    self.user_id,
                    f"⏱ {symbol.upper()} отслеживался 12 часов.\nИзменение: {change_percent:.2f}%\nТекущая цена: {current_price}",
                )
                to_remove.append(symbol)

        for symbol in to_remove:
            del self.tracked[symbol]
