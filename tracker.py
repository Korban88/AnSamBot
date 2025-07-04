import asyncio
import time
from pycoingecko import CoinGeckoAPI

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked = {}
        self.running = False

    def start_tracking(self, coin_id, entry_price):
        self.tracked[coin_id] = {
            "entry": entry_price,
            "start": time.time(),
            "notified_3_5": False,
            "notified_5": False,
        }

    def stop_all_tracking(self):
        self.tracked.clear()

    def run(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def _loop(self):
        while True:
            if not self.tracked:
                await asyncio.sleep(10)
                continue

            for coin_id in list(self.tracked.keys()):
                try:
                    price = await self.get_price(coin_id)
                    data = self.tracked[coin_id]
                    entry = data["entry"]
                    now = time.time()
                    change_percent = (price - entry) / entry * 100

                    if not data["notified_3_5"] and change_percent >= 3.5:
                        await self.bot.send_message(
                            self.user_id,
                            f"📈 Монета <b>{coin_id}</b> выросла на <b>+3.5%</b>!\nТекущая цена: <b>{price:.4f}$</b>"
                        )
                        data["notified_3_5"] = True

                    if not data["notified_5"] and change_percent >= 5:
                        await self.bot.send_message(
                            self.user_id,
                            f"🚀 Монета <b>{coin_id}</b> достигла цели <b>+5%</b>!\nЦена: <b>{price:.4f}$</b>"
                        )
                        data["notified_5"] = True

                    if now - data["start"] >= 43200:  # 12 часов
                        if not data["notified_5"]:
                            diff = round(change_percent, 2)
                            await self.bot.send_message(
                                self.user_id,
                                f"🕛 12 часов отслеживания <b>{coin_id}</b> завершены.\nИзменение за период: <b>{diff}%</b>.\nЦена: {price:.4f}$"
                            )
                        self.tracked.pop(coin_id)

                except Exception as e:
                    print(f"Ошибка при отслеживании {coin_id}: {e}")
            await asyncio.sleep(60)

    async def get_price(self, coin_id):
        cg = CoinGeckoAPI()
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return float(data[coin_id]["usd"])
