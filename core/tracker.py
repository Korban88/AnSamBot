import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from core.database import Database

class PriceTracker:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
    
    async def check_prices(self):
        trackings = self.db.get_active_trackings()
        
        for tracking in trackings:
            coin_id, entry_price, start_time, user_id, notified_3_5, notified_5 = tracking
            
            # Получаем текущую цену (реализация ниже)
            current_price = await self._get_current_price(coin_id)
            
            # Расчет изменений
            change_percent = (current_price - entry_price) / entry_price * 100
            elapsed = datetime.now() - datetime.fromisoformat(start_time)
            
            # Уведомления
            if change_percent >= 5 and not notified_5:
                await self._notify_user(user_id, f"🚀 {coin_id} +5%!")
                self.db.mark_notified(coin_id, target="5%")
                
            elif change_percent >= 3.5 and not notified_3_5:
                await self._notify_user(user_id, f"📈 {coin_id} +3.5%")
                self.db.mark_notified(coin_id, target="3.5%")
