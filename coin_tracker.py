import time
import asyncio
import logging
from datetime import datetime, timedelta
from crypto_utils import get_price_by_symbol

logger = logging.getLogger(__name__)

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}  # symbol: {start_time, start_price, notified_3_5, notified_5}

    async def track_coin(self, symbol):
        price = get_price_by_symbol(symbol)
        if price is None:
            await self.bot.send_message(self.user_id, f"❌ Не удалось получить цену {symbol}")
            return

        self.tracked[symbol] = {
            "start_price": price,
            "start_time": datetime.utcnow(),
            "notified_3_5": False,
            "notified_5": False
        }
        await self.bot.send_message(self.user_id, f"👁 Начал отслеживать {symbol} по цене {price} USD")

    async def check_prices(self):
        to_remove = []

        for symbol, data in self.tracked.items():
            current_price = get_price_by_symbol(symbol)
            if current_price is None:
                continue

            change = ((current_price - data["start_price"]) / data["start_price"]) * 100
            now = datetime.utcnow()
            elapsed = now - data["start_time"]

            if change >= 5 and not data["notified_5"]:
                await self.bot.send_message(self.user_id, f"🚀 {symbol} вырос на +5%! Текущая цена: {current_price} USD")
                data["notified_5"] = True
                to_remove.append(symbol)

            elif change >= 3.5 and not data["notified_3_5"]:
                await self.bot.send_message(self.user_id, f"📈 {symbol} вырос на +3.5%! Текущая цена: {current_price} USD")
                data["notified_3_5"] = True

            elif elapsed >= timedelta(hours=12):
                direction = "выросла" if change > 0 else "упала"
                await self.bot.send_message(
                    self.user_id,
                    f"⏱ 12 часов наблюдения за {symbol}. Она {direction} на {round(change, 2)}%. Текущая цена: {current_price} USD"
                )
                to_remove.append(symbol)

        for symbol in to_remove:
            self.tracked.pop(symbol, None)
