import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    OWNER_ID: int
    
    class Config:
        env_file = ".env"
        case_sensitive = True

config = Settings()
