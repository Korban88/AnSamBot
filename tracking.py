import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from crypto_utils import get_current_price
from crypto_list import TELEGRAM_WALLET_COIN_IDS
import json
import os
import logging
import pytz

TRACKING_FILE = "tracking_data.json"
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

class CoinTracker:
    tracked = {}

    @staticmethod
    def get_coin_id(symbol):
        for cid, sym in TELEGRAM_WALLET_COIN_IDS.items():
            if sym.lower() == symbol.lower():
                return cid
        return None

    @staticmethod
    def track(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        now = datetime.now(MOSCOW_TZ)
        coin_id = CoinTracker.get_coin_id(symbol)
        if not coin_id:
            logging.error(f"❌ Не найден CoinGecko ID для {symbol}")
            return

        CoinTracker.tracked.setdefault(str(user_id), {})[symbol] = {
            "symbol": symbol,
            "coin_id": coin_id,
            "start_time": now.isoformat(),
            "initial_price": None,
            "notified_approaching_3_5": False,
            "notified_reached_3_5": False,
            "notified_reached_5": False,
            "notified_near_stop_loss": False,
            "notified_hit_stop_loss": False,
            "notified_12h": False,
            "ttl_hours": 48  # жёсткий срок жизни сигнала
        }
        CoinTracker.save_tracking_data()
        logging.info(f"✅ Добавлено отслеживание: {symbol.upper()} (ID: {coin_id})")

        async def set_initial_price():
            attempts = 0
            while attempts < 3:
                price = await get_current_price(coin_id)
                if price:
                    CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = price
                    CoinTracker.save_tracking_data()
                    logging.info(f"📌 Начальная цена {symbol.upper()} установлена: {price}")
                    return
                attempts += 1
                logging.warning(f"⚠️ Попытка {attempts} не удалась для {symbol.upper()}, пробуем снова...")
                await asyncio.sleep(20)
            CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = "fetch_error"
            CoinTracker.save_tracking_data()
            logging.error(f"❌ Не удалось получить цену для {symbol.upper()} после 3 попыток")

        asyncio.create_task(set_initial_price())
        asyncio.create_task(CoinTracker.monitor(user_id, symbol, context))

    @staticmethod
    async def monitor(user_id, symbol, context: ContextTypes.DEFAULT_TYPE):
        await asyncio.sleep(10)
        start_time = datetime.now(MOSCOW_TZ)

        coin_id = CoinTracker.tracked[str(user_id)][symbol].get("coin_id")
        if not coin_id:
            return

        initial_price = CoinTracker.tracked[str(user_id)][symbol].get("initial_price")
        if not initial_price or initial_price == "fetch_error":
            initial_price = await get_current_price(coin_id)
            if initial_price:
                CoinTracker.tracked[str(user_id)][symbol]["initial_price"] = initial_price
                CoinTracker.save_tracking_data()

        while True:
            await asyncio.sleep(600)

            current_price = await get_current_price(coin_id)
            if current_price is None or not initial_price or initial_price == "fetch_error":
                continue

            percent_change = ((current_price - initial_price) / initial_price) * 100
            coin_data = CoinTracker.tracked[str(user_id)][symbol]

            # 🎯 Цели вверх
            if percent_change >= 5 and not coin_data["notified_reached_5"]:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🚀 {symbol.upper()} выросла на +5%!\nТекущая цена: ${current_price:.4f}"
                )
                coin_data["notified_reached_5"] = True
                CoinTracker.tracked[str(user_id)].pop(symbol, None)
                CoinTracker.save_tracking_data()
                break

            elif percent_change >= 3.5 and not coin_data["notified_reached_3_5"]:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎯 {symbol.upper()} достигла +3.5%!\nТекущая цена: ${current_price:.4f}"
                )
                coin_data["notified_reached_3_5"] = True
                CoinTracker.save_tracking_data()

            elif percent_change >= 3 and not coin_data["notified_approaching_3_5"]:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔔 {symbol.upper()} приближается к цели (+3.5%). Текущая цена: ${current_price:.4f}"
                )
                coin_data["notified_approaching_3_5"] = True
                CoinTracker.save_tracking_data()

            # ⛔ Стоп-логика вниз
            elif percent_change <= -3 and not coin_data["notified_hit_stop_loss"]:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⛔ {symbol.upper()} сработал стоп-лосс (−3%). Рекомендация: выйти.\nТекущая цена: ${current_price:.4f}"
                )
                coin_data["notified_hit_stop_loss"] = True
                CoinTracker.tracked[str(user_id)].pop(symbol, None)
                CoinTracker.save_tracking_data()
                break

            elif percent_change <= -2 and not coin_data["notified_near_stop_loss"]:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📉 {symbol.upper()} близко к стоп-лоссу (−2%). Будь аккуратен.\nТекущая цена: ${current_price:.4f}"
                )
                coin_data["notified_near_stop_loss"] = True
                CoinTracker.save_tracking_data()

            # 🕑 Временные события: 12ч апдейт + TTL 48ч
            elapsed = (datetime.now(MOSCOW_TZ) - start_time)
            if elapsed >= timedelta(hours=12) and not coin_data.get("notified_12h"):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"ℹ️ 12 часов с момента входа по {symbol.upper()}. Текущая динамика: {percent_change:.2f}%."
                )
                coin_data["notified_12h"] = True
                CoinTracker.save_tracking_data()

            ttl_hours = coin_data.get("ttl_hours", 48)
            if elapsed >= timedelta(hours=ttl_hours):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🚫 Сигнал по {symbol.upper()} истёк (без достижения цели за {ttl_hours}ч). "
                         f"Рекомендация: выйти и перераспределить капитал."
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
        try:
            with open(TRACKING_FILE, "w") as f:
                json.dump(CoinTracker.tracked, f, indent=2)
        except Exception as e:
            logging.error(f"❌ Ошибка при сохранении tracking_data.json: {e}")

    @staticmethod
    def load_tracking_data():
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, "r") as f:
                    CoinTracker.tracked = json.load(f)
            except Exception as e:
                logging.error(f"❌ Ошибка при загрузке tracking_data.json: {e}")
                CoinTracker.tracked = {}
        else:
            CoinTracker.tracked = {}

    @staticmethod
    async def evening_report(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, coins in CoinTracker.tracked.items():
            if not coins:
                continue
            report_lines = ["📊 Вечерний отчёт:"]
            for symbol, data in coins.items():
                coin_id = data.get("coin_id")
                current_price = await get_current_price(coin_id)
                if not current_price or not data.get("initial_price") or data["initial_price"] == "fetch_error":
                    continue
                percent_change = ((current_price - data["initial_price"]) / data["initial_price"]) * 100

                if percent_change >= 4.5:
                    status = "🚀 почти у цели — можно зафиксировать"
                elif percent_change >= 3.5:
                    status = "✅ близко к цели — держать"
                elif percent_change <= -2:
                    status = "⚠️ близко к стоп-лоссу — подумай о выходе"
                else:
                    status = "ℹ️ умеренное движение — держать"

                start_time_local = datetime.fromisoformat(data["start_time"]).astimezone(MOSCOW_TZ)
                report_lines.append(
                    f"{symbol.upper()} — {percent_change:.2f}% | {status} "
                    f"(цена: ${current_price:.4f}, старт: {start_time_local.strftime('%H:%M')})"
                )

            if len(report_lines) > 1:
                await context.bot.send_message(chat_id=int(user_id), text="\n".join(report_lines))

    @staticmethod
    def run(context: ContextTypes.DEFAULT_TYPE):
        CoinTracker.load_tracking_data()
        for user_id, coins in CoinTracker.tracked.items():
            for symbol in coins.keys():
                asyncio.create_task(CoinTracker.monitor(int(user_id), symbol, context))
