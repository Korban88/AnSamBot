import asyncio
from crypto_utils import get_price

TRACKING = {}

async def start_tracking(symbol, context):
    if symbol in TRACKING:
        return

    async def track():
        start_price = await get_price(symbol)
        if not start_price:
            return
        start_time = asyncio.get_event_loop().time()

        while True:
            await asyncio.sleep(600)
            current_price = await get_price(symbol)
            if not current_price:
                continue

            growth = (current_price - start_price) / start_price * 100
            if growth >= 5:
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=f"✅ {symbol} вырос на +5% — {round(current_price, 4)} $"
                )
                break
            elif growth >= 3.5:
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=f"📈 {symbol} уже +3.5% — {round(current_price, 4)} $"
                )

            if asyncio.get_event_loop().time() - start_time > 43200:
                change = round((current_price - start_price) / start_price * 100, 2)
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=f"⏰ {symbol} не вырос за 12ч. Динамика: {change}%"
                )
                break

        del TRACKING[symbol]

    TRACKING[symbol] = asyncio.create_task(track())

def stop_all_trackings():
    for task in TRACKING.values():
        task.cancel()
    TRACKING.clear()
