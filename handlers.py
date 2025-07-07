from aiogram import Dispatcher, types

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        await message.answer("Добро пожаловать в AnSam Bot!")

    # Добавьте другие обработчики по аналогии
