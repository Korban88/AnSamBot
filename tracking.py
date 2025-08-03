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
        CoinTracker.tracked.setdefault(str(user_id), {})[symbol] = {
            "symbol": symbol,
            "start_time": now.isoformat(),
            "initial_price": None
        }
        CoinTracker.save_tracking_data()
        asyncio.create_task(CoinTracker.monitor(user_id, symbol, context))

    @staticmethod
    async def monitor(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(10)
        start_time = datetime.utcnow()

        initial_price = await get_current_price(symbol)
        CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = initial_price
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
                CoinTracker.tracked[str(user_id)].pop(symbol, None)
                CoinTracker.save_tracking_data()
                break

            elif percent_change >= 3.5:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔔 {symbol.upper()} приближается к цели (+3.5%). Текущая цена: ${current_price:.4f}"
                )

            elapsed = datetime.utcnow() - start_time
            if elapsed >= timedelta(hours=12):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ С момента отслеживания прошло 12 часов.\nИзменение цены {symbol.upper()}: {percent_change:.2f}%"
                )
                CoinTracker.tracked[str(user_id)].pop(symbol, None)
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
    async def evening_report(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, coins in CoinTracker.tracked.items():
            if not coins:
                continue
            report_lines = ["📊 Вечерний отчёт:"]
            for symbol, data in coins.items():
                current_price = await get_current_price(symbol)
                if not current_price or not data.get("initial_price"):
                    continue
                percent_change = ((current_price - data["initial_price"]) / data["initial_price"]) * 100

                # Определяем рекомендацию
                if percent_change >= 4.5:
                    status = "🚀 почти у цели — можно зафиксировать"
                elif percent_change >= 3.5:
                    status = "✅ близко к цели — держать"
                elif percent_change <= -2:
                    status = "⚠️ близко к стоп-лоссу — подумай о выходе"
                else:
                    status = "ℹ️ умеренное движение — держать"

                report_lines.append(f"{symbol.upper()} — {percent_change:.2f}% | {status}")

            if len(report_lines) > 1:
                await context.bot.send_message(chat_id=int(user_id), text="\n".join(report_lines))

    @staticmethod
    def run(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, coins in CoinTracker.tracked.items():
            for symbol in coins.keys():
                asyncio.create_task(CoinTracker.monitor(int(user_id), symbol, context))
