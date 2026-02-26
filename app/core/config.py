from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "1Charge Chatbot"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "your-secret-key-keep-it-safe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    # Database
    DB_HOST: str = "localhost"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "breakdown_db"
    DB_PORT: int = 3306

    # OpenAI
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
