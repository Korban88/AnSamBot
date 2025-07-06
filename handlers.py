from aiogram import Dispatcher, types
from core.database import Database

db = Database()

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start_cmd(message: types.Message):
        await message.answer("Welcome to AnSam Crypto Bot!")
    
    @dp.message_handler(text="Get Signal")
    async def get_signal(message: types.Message):
        # Логика обработки
        pass
