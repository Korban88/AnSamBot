import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from crypto_utils import get_current_price
import json
import os
import logging

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
        logging.info(f"✅ Добавлено отслеживание: {symbol.upper()} для пользователя {user_id}")

        # сразу пробуем подтянуть цену
        async def set_initial_price():
            price = await get_current_price(symbol)
            if price:
                CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = price
                CoinTracker.save_tracking_data()
                logging.info(f"📌 Начальная цена {symbol.upper()} установлена сразу: {price}")
            else:
                logging.warning(f"⚠️ Не удалось сразу получить цену для {symbol.upper()}, повторим через 30 сек")
                await asyncio.sleep(30)
                price_retry = await get_current_price(symbol)
                if price_retry:
                    CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = price_retry
                    CoinTracker.save_tracking_data()
                    logging.info(f"📌 Цена {symbol.upper()} успешно получена повторно: {price_retry}")
                else:
                    logging.error(f"❌ Не удалось получить цену для {symbol.upper()} даже после повторной попытки")

        asyncio.create_task(set_initial_price())
        asyncio.create_task(CoinTracker.monitor(user_id, symbol, context))

    @staticmethod
    async def monitor(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(10)
        start_time = datetime.utcnow()

        initial_price = CoinTracker.tracked[str(user_id)][symbol].get("initial_price")
        if not initial_price:
            initial_price = await get_current_price(symbol)
            if initial_price:
                CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = initial_price
                CoinTracker.save_tracking_data()
                logging.info(f"📌 (monitor) Цена {symbol.upper()} установлена: {initial_price}")

        while True:
            await asyncio.sleep(600)  # каждые 10 минут

            current_price = await get_current_price(symbol)
            if current_price is None or not initial_price:
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
        logging.info("⛔ Все отслеживания удалены")

    @staticmethod
    def save_tracking_data():
        try:
            with open(TRACKING_FILE, "w") as f:
                json.dump(CoinTracker.tracked, f, indent=2)
            logging.info(f"💾 Сохранены отслеживания: {CoinTracker.tracked}")
        except Exception as e:
            logging.error(f"❌ Ошибка при сохранении tracking_data.json: {e}")

    @staticmethod
    def load_tracking_data():
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, "r") as f:
                    CoinTracker.tracked = json.load(f)
                logging.info(f"📂 Загружено отслеживаний: {CoinTracker.tracked}")
            except Exception as e:
                logging.error(f"❌ Ошибка при загрузке tracking_data.json: {e}")
                CoinTracker.tracked = {}
        else:
            CoinTracker.tracked = {}
            logging.info("⚠️ tracking_data.json не найден — старт с пустого списка")

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
                    logging.warning(f"⚠️ Нет данных для {symbol.upper()} в отчёте")
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

                report_lines.append(f"{symbol.upper()} — {percent_change:.2f}% | {status} (цена: ${current_price:.4f})")

            if len(report_lines) > 1:
                await context.bot.send_message(chat_id=int(user_id), text="\n".join(report_lines))
                logging.info(f"✅ Вечерний отчёт отправлен пользователю {user_id}")

    @staticmethod
    def run(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, coins in CoinTracker.tracked.items():
            for symbol in coins.keys():
                asyncio.create_task(CoinTracker.monitor(int(user_id), symbol, context))
