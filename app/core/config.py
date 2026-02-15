from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal

class Settings(BaseSettings):
    DATABASE_URL:str
    DB_POOL_SIZE:int=5
    DB_MAX_OVERFLOW:int=10
    SECRET_KEY:str
    ALGORITHM:str="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int=30
    REFRESH_TOKEN_EXPIRE_DAYS:int=7
    PASSWORD_HASH_SCHEME:str="argon2"
    
    OPENAI_API_KEY:str
    OPENAI_MODEL:str
    OPENAI_TIMEOUT:int=30

    DEBUG:bool=True
    ENV: Literal["development", "staging", "production"] = "development"

    class Config:
        env_file = ".env"
        env_file_encoding="utf-8"
    
@lru_cache
def get_settings()->Settings:

    return Settings()

