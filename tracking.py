import asyncio
import time
import logging

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
        logging.info(f"✅ Начато отслеживание {coin_id} по цене {entry_price}")

    def stop_all_tracking(self):
        logging.info("⛔️ Остановлены все отслеживания.")
        self.tracked.clear()

    def run(self):
        if not self.running:
            self.running = True
            asyncio.create_task(self._loop())
            logging.info("▶️ Цикл отслеживания запущен.")

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
                            f"📈 Монета <b>{coin_id}</b> выросла на <b>+3.5%</b>!\nТекущая цена: <b>{price}$</b>"
                        )
                        data["notified_3_5"] = True
                        logging.info(f"🔔 {coin_id}: уведомление +3.5% отправлено")

                    if not data["notified_5"] and change_percent >= 5:
                        await self.bot.send_message(
                            self.user_id,
                            f"🚀 Монета <b>{coin_id}</b> достигла цели <b>+5%</b>!\nЦена: <b>{price}$</b>"
                        )
                        data["notified_5"] = True
                        logging.info(f"🎯 {coin_id}: достигнута цель +5%")

                    if now - data["start"] >= 43200:  # 12 часов
                        if not data["notified_5"]:
                            diff = round(change_percent, 2)
                            await self.bot.send_message(
                                self.user_id,
                                f"🕛 12 часов отслеживания {coin_id} завершены.\nИзменение: {diff}%\nЦена: {price}$"
                            )
                        self.tracked.pop(coin_id)
                        logging.info(f"📤 {coin_id}: отслеживание завершено спустя 12 часов")

                except Exception as e:
                    logging.error(f"❌ Ошибка при отслеживании {coin_id}: {e}")
            await asyncio.sleep(60)

    async def get_price(self, coin_id):
        from pycoingecko import CoinGeckoAPI
        cg = CoinGeckoAPI()
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return float(data[coin_id]["usd"])
