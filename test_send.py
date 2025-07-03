import asyncio
from aiogram import Bot

BOT_TOKEN = "8148906065:AAEw8yAPKnhjw3AK2tsYEo-h9LVj74xJS4c"
USER_ID = 347552741

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(USER_ID, "Тестовое сообщение от бота")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
