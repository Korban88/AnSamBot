import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    OWNER_ID: int = int(os.getenv("OWNER_ID", 0))
    
    class Config:
        env_file = ".env"  # Для локальной разработки

config = Settings()
