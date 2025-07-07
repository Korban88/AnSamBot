import os

class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.OWNER_ID = os.getenv("OWNER_ID")
        
        if not self.TELEGRAM_TOKEN or not self.OWNER_ID:
            raise ValueError("Не заданы обязательные переменные окружения")

config = Config()
