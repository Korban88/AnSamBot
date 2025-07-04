import asyncio
from datetime import datetime, timedelta

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.active_trackings = {}

    async def track_coin(self, symbol, start_price):
        if symbol in self.active_trackings:
            return

        self.active_trackings[symbol] = {
            'start_time': datetime.utcnow(),
            'start_price': start_price
        }

        asyncio.create_task(self._monitor(symbol))

    async def stop_all_tracking(self):
        self.active_trackings.clear()

    async def _monitor(self, symbol):
        data = self.active_trackings.get(symbol)
        if not data:
            return

        start_price = data['start_price']
        start_time = data['start_time']

        while True:
            await asyncio.sleep(600)  # каждые 10 минут

            # Импортировать здесь, чтобы избежать циклического импорта
            from crypto_utils import get_price

            current_price = get_price(symbol)
            if not current_price:
                continue

            change = ((current_price - start_price) / start_price) * 100

            # Уведомление при +3.5%
            if 3.4 < change < 3.6:
                await self.bot.send_message(
                    self.user_id,
                    f"📈 {symbol} вырос на *{change:.2f}%*. Монета близка к цели +5%!"
                )

            # Уведомление при +5%
            if change >= 5:
                await self.bot.send_message(
                    self.user_id,
                    f"🚀 {symbol} достиг цели роста *+5%*! Цена: *{current_price}*"
                )
                self.active_trackings.pop(symbol, None)
                return

            # Уведомление через 12 часов, если +3.5% не достигнуты
            if datetime.utcnow() - start_time >= timedelta(hours=12):
                await self.bot.send_message(
                    self.user_id,
                    f"⏰ Прошло 12 часов с начала отслеживания {symbol}.\n"
                    f"Текущая цена: *{current_price}*,\n"
                    f"Изменение с начала: *{change:.2f}%*"
                )
                self.active_trackings.pop(symbol, None)
                return
