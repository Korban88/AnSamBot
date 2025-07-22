import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from crypto_utils import get_current_price
import json
import os

TRACKING_FILE = "tracking_data.json"

class CoinTracker:
    tracked = {}

    @staticmethod
    def track(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        now = datetime.utcnow()
        CoinTracker.tracked[user_id] = {
            "symbol": symbol,
            "start_time": now.isoformat(),
            "initial_price": None
        }
        CoinTracker.save_tracking_data()
        asyncio.create_task(CoinTracker.monitor(user_id, symbol, context))

    @staticmethod
    async def monitor(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(10)  # чтобы не вызывалось мгновенно
        start_time = datetime.utcnow()

        # Получаем стартовую цену
        initial_price = await get_current_price(symbol)
        CoinTracker.tracked[user_id]["initial_price"] = initial_price
        CoinTracker.save_tracking_data()

        while True:
            await asyncio.sleep(600)  # каждые 10 минут

            current_price = await get_current_price(symbol)
            if current_price is None or initial_price is None:
                continue

            percent_change = ((current_price - initial_price) / initial_price) * 100

            if percent_change >= 5:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🚀 {symbol.upper()} выросла на +5%!\nТекущая цена: ${current_price:.4f}"
                )
                CoinTracker.tracked.pop(user_id, None)
                CoinTracker.save_tracking_data()
                break

            elif percent_change >= 3.5:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔔 {symbol.upper()} приближается к цели (+3.5%). Текущая цена: ${current_price:.4f}"
                )

            # проверка 12 часов
            elapsed = datetime.utcnow() - start_time
            if elapsed >= timedelta(hours=12):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ С момента отслеживания прошло 12 часов.\nИзменение цены {symbol.upper()}: {percent_change:.2f}%"
                )
                CoinTracker.tracked.pop(user_id, None)
                CoinTracker.save_tracking_data()
                break

    @staticmethod
    def clear_all():
        CoinTracker.tracked.clear()
        CoinTracker.save_tracking_data()

    @staticmethod
    def save_tracking_data():
        with open(TRACKING_FILE, "w") as f:
            json.dump(CoinTracker.tracked, f)

    @staticmethod
    def load_tracking_data():
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, "r") as f:
                CoinTracker.tracked = json.load(f)

    @staticmethod
    def run(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, data in CoinTracker.tracked.items():
            symbol = data["symbol"]
            asyncio.create_task(CoinTracker.monitor(user_id, symbol, context))
