import asyncio
from datetime import datetime, timedelta

tracking_tasks = {}

async def start_tracking(bot, user_id, coin_id, start_price):
    async def track():
        start_time = datetime.now()
        initial_price = start_price

        while True:
            await asyncio.sleep(600)  # 10 минут
            
            # Симуляция получения новой цены (замени на реальный API)
            new_price = await get_price(coin_id)
            if not new_price:
                continue

            price_change = ((new_price - initial_price) / initial_price) * 100
            
            # Уведомление о росте на 3.5%
            if price_change >= 3.5:
                await bot.send_message(user_id, f"🚀 {coin_id} выросла на +{round(price_change, 2)}%! Текущая цена: {new_price} $")
                break

            # По истечении 12 часов — финальный отчёт
            if datetime.now() - start_time >= timedelta(hours=12):
                result = "выросла" if price_change > 0 else "упала" if price_change < 0 else "не изменилась"
                await bot.send_message(
                    user_id,
                    f"⏱ За 12 часов монета {coin_id} {result}.\nИзменение: {round(price_change, 2)}% (с {initial_price} $ до {new_price} $)"
                )
                break

    task = asyncio.create_task(track())
    tracking_tasks.setdefault(user_id, []).append(task)


async def get_price(coin_id):
    # Тут должен быть реальный запрос к API. Сейчас — фейковый возврат для теста
    import random
    return round(random.uniform(0.95, 1.05), 4)

def stop_all_trackings(user_id):
    tasks = tracking_tasks.get(user_id, [])
    for task in tasks:
        task.cancel()
    tracking_tasks[user_id] = []
