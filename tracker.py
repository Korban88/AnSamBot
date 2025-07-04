import asyncio
import logging
from datetime import datetime, timedelta

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}  # coin_id -> {'start_price': float, 'start_time': datetime}

    async def load_state(self):
        # Заглушка. В будущем: восстановление состояния из БД или файла
        pass

    def start_tracking(self, coin_id, price):
        self.tracked[coin_id] = {
            'start_price': price,
            'start_time': datetime.utcnow()
        }

    def stop_all(self):
        self.tracked.clear()

    async def _check_prices(self):
        from crypto_utils import get_price

        to_remove = []
        for coin_id, data in self.tracked.items():
            try:
                current_price = await get_price(coin_id)
                start_price = data['start_price']
                start_time = data['start_time']
                percent_change = ((current_price - start_price) / start_price) * 100

                if percent_change >= 5:
                    await self.bot.send_message(
                        self.user_id,
                        f"📈 Монета {coin_id} выросла на +5%.\nЦена сейчас: {current_price:.4f} $"
                    )
                    to_remove.append(coin_id)
                elif datetime.utcnow() - start_time > timedelta(hours=12):
                    change_str = f"{percent_change:+.2f}%"
                    await self.bot.send_message(
                        self.user_id,
                        f"🕛 12 часов прошло с начала отслеживания {coin_id}.\nИзменение: {change_str}\nЦена сейчас: {current_price:.4f} $"
                    )
                    to_remove.append(coin_id)
            except Exception as e:
                logging.exception(f"Ошибка при проверке цены {coin_id}: {e}")
                to_remove.append(coin_id)

        for coin_id in to_remove:
            self.tracked.pop(coin_id, None)

    async def _loop(self):
        while True:
            await self._check_prices()
            await asyncio.sleep(600)

    def run(self):
        asyncio.create_task(self._loop())
