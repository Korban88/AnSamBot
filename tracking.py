import asyncio
import httpx
import logging
from config import OWNER_ID
from crypto_utils import get_current_price

class CoinTracker:
    def __init__(self, bot, coin, start_price):
        self.bot = bot
        self.coin = coin
        self.start_price = start_price
        self.tracking_time = 0  # в минутах

    async def track(self):
        while self.tracking_time < 720:  # 12 часов = 720 минут
            try:
                current_price = await get_current_price(self.coin["id"])
                if not current_price:
                    logging.warning(f"Не удалось получить цену для {self.coin['symbol']}")
                    break

                percent_change = ((current_price - self.start_price) / self.start_price) * 100

                if percent_change >= 5:
                    await self.bot.send_message(
                        OWNER_ID,
                        f"🚀 Монета {self.coin['symbol']} выросла на 5%!\n\n"
                        f"🔹 Старт: {self.start_price:.4f} USD\n"
                        f"🔹 Текущая цена: {current_price:.4f} USD\n"
                        f"🔹 Рост: {percent_change:.2f}%"
                    )
                    break

                elif percent_change >= 3.5:
                    await self.bot.send_message(
                        OWNER_ID,
                        f"📈 Монета {self.coin['symbol']} приближается к цели: +3.5%\n\n"
                        f"🔹 Старт: {self.start_price:.4f} USD\n"
                        f"🔹 Текущая цена: {current_price:.4f} USD\n"
                        f"🔹 Рост: {percent_change:.2f}%"
                    )

                self.tracking_time += 10
                await asyncio.sleep(600)  # 10 минут

            except Exception as e:
                logging.error(f"Ошибка при отслеживании {self.coin['symbol']}: {e}")
                break

        # Если прошло 12 часов и цель не достигнута
        if self.tracking_time >= 720:
            final_price = await get_current_price(self.coin["id"])
            if final_price:
                final_change = ((final_price - self.start_price) / self.start_price) * 100
                await self.bot.send_message(
                    OWNER_ID,
                    f"⏰ Прошло 12 часов. Монета {self.coin['symbol']} не достигла цели.\n\n"
                    f"🔹 Старт: {self.start_price:.4f} USD\n"
                    f"🔹 Конец: {final_price:.4f} USD\n"
                    f"🔹 Изменение: {final_change:.2f}%"
                )

# Фоновый планировщик (используется в main.py)
class CoinTrackingManager:
    def __init__(self):
        self.trackers = []

    def add_tracker(self, tracker):
        self.trackers.append(tracker)

    async def run(self):
        tasks = [tracker.track() for tracker in self.trackers]
        await asyncio.gather(*tasks)
