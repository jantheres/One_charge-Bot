
import os
from decouple import config

class Settings:
    PROJECT_NAME: str = "1Charge Chatbot"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-keep-it-safe")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DB_HOST: str = config("DB_HOST", default="railway")
    DB_USER: str = config("DB_USER", default="mysql-4fvs.railway.internal")
    DB_PASSWORD: str = config("DB_PASSWORD", default="")
    DB_NAME: str = config("DB_NAME", default="railway")
    DB_PORT: int = config("DB_PORT", default=3306, cast=int)

    # OpenAI
    OPENAI_API_KEY: str = config("OPENAI_API_KEY", default="")

settings = Settings()
