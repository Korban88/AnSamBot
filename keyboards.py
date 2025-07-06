from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Получить ещё сигнал"),
        KeyboardButton("Остановить все отслеживания"),
        KeyboardButton("Старт")
    )
    return keyboard
