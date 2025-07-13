import asyncio

# Простейшая структура кеша для отслеживания
TRACKING = {}

async def start_tracking_coin(coin_id: str, user_id: int):
    if user_id not in TRACKING:
        TRACKING[user_id] = []
    TRACKING[user_id].append({"coin_id": coin_id, "start_time": asyncio.get_event_loop().time()})
    # Здесь должен быть запуск реального отслеживания с проверкой каждые 10 минут и отправкой уведомлений

async def stop_all_trackings(user_id: int):
    if user_id in TRACKING:
        del TRACKING[user_id]
    # Здесь должен быть реальный механизм остановки задач asyncio если он внедрён
