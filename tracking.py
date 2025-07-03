import time
from threading import Thread
from pycoingecko import CoinGeckoAPI
from aiogram.utils.markdown import hbold

cg = CoinGeckoAPI()

class CoinTracker:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.tracked_coins = {}
        self.running = False

    def start_tracking(self, coin_id, start_price):
        self.tracked_coins[coin_id] = {
            "start_price": start_price,
            "start_time": time.time()
        }

    def stop_all_tracking(self):
        self.tracked_coins = {}

    def get_price(self, coin_id):
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return data.get(coin_id, {}).get('usd')

    def track_loop(self):
        self.running = True
        while self.running:
            to_remove = []
            for coin_id, data in self.tracked_coins.items():
                current_price = self.get_price(coin_id)
                if current_price is None:
                    continue

                start_price = data["start_price"]
                change_percent = ((current_price - start_price) / start_price) * 100
                elapsed = time.time() - data["start_time"]

                if change_percent >= 5:
                    msg = f"🚀 Монета {coin_id.upper()} выросла на +5%!\nЦена: {hbold(round(current_price, 4))} $"
                    self.bot.loop.create_task(self.bot.send_message(self.user_id, msg))
                    to_remove.append(coin_id)

                elif elapsed >= 12 * 3600:
                    msg = f"⏰ Монета {coin_id.upper()} не показала роста за 12 часов.\nТекущая цена: {hbold(round(current_price, 4))} $\nИзменение: {round(change_percent, 2)}%"
                    self.bot.loop.create_task(self.bot.send_message(self.user_id, msg))
                    to_remove.append(coin_id)

            for coin_id in to_remove:
                del self.tracked_coins[coin_id]

            time.sleep(600)  # каждые 10 минут

    def run(self):
        t = Thread(target=self.track_loop)
        t.start()
