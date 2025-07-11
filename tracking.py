import threading
from config import TRACKING_ALERT_PERCENT
from crypto_utils import get_current_price

tracking_threads = {}

def start_tracking_coin(coin_id, bot):
    if coin_id in tracking_threads:
        return
    thread = threading.Thread(target=track_coin_price, args=(coin_id, bot), daemon=True)
    tracking_threads[coin_id] = thread
    thread.start()

def track_coin_price(coin_id, bot):
    initial_price = get_current_price(coin_id)
    if not initial_price:
        return
    while True:
        current_price = get_current_price(coin_id)
        if current_price:
            percent_change = ((current_price - initial_price) / initial_price) * 100
            if percent_change >= TRACKING_ALERT_PERCENT:
                bot.send_message(chat_id=347552741, text=f"💹 {coin_id}: рост более {TRACKING_ALERT_PERCENT}%!")
                break


def stop_all_trackings():
    tracking_threads.clear()
