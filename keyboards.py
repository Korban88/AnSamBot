from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Получить ещё сигнал"),
        KeyboardButton("Остановить все отслеживания")
    )
    return keyboard
