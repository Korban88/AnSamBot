import asyncio
from aiogram import Bot, Dispatcher, executor, types
from config import config
from core.signals import generate_daily_signal
from core.tracking import start_tracking
from utils.logger import TradeLogger

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(bot)
logger = TradeLogger(bot)

@dp.message_handler(commands=['start'])
async def send_signal(message: types.Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply("⛔ Доступ только для владельца")
    
    signal = await generate_daily_signal()
    await message.reply(signal['formatted'])
    await start_tracking(signal, bot)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
