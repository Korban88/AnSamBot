import logging
from aiogram import Bot, Dispatcher, executor, types
from core.signals import generate_daily_signal
from config import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_signal(message: types.Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply("⛔ Доступ запрещен")
    
    signal = await generate_daily_signal()
    if signal:
        await message.reply(
            f"🚀 {signal['coin']} сигнал\n"
            f"💰 Цена: ${signal['price']:.2f}\n"
            f"🎯 Цель: ${signal['target']:.2f} (+5%)\n"
            f"🛑 Стоп: ${signal['stop_loss']:.2f}\n"
            f"📊 RSI: {signal['rsi']:.1f}"
        )
    else:
        await message.reply("Сегодня нет хороших сигналов")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
