import logging
from crypto_utils import get_top_coins

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}

    async def add(self, symbol):
        price = await self._get_price(symbol)
        if price:
            self.tracked[symbol] = {
                "start_price": price,
                "start_time": self._current_timestamp()
            }

    async def clear(self):
        self.tracked = {}

    async def run(self):
        if not self.tracked:
            return

        coins = get_top_coins()
        prices = {c["symbol"]: c["current_price"] for c in coins}

        to_notify = []

        for symbol, data in list(self.tracked.items()):
            current = prices.get(symbol)
            if not current:
                continue

            start = data["start_price"]
            delta = (current - start) / start * 100
            elapsed = self._current_timestamp() - data["start_time"]

            if delta >= 5:
                to_notify.append(f"🎯 {symbol} вырос на +{round(delta, 2)}% — цель достигнута!")
                del self.tracked[symbol]
            elif elapsed > 12 * 3600:
                to_notify.append(f"⏱ {symbol} не вырос за 12ч. Динамика: {round(delta, 2)}%")
                del self.tracked[symbol]

        for msg in to_notify:
            await self.bot.send_message(self.user_id, msg)

    async def _get_price(self, symbol):
        coins = get_top_coins()
        for c in coins:
            if c["symbol"] == symbol:
                return c["current_price"]
        return None

    def _current_timestamp(self):
        import time
        return int(time.time())
