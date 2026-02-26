from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "1Charge Chatbot"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "your-secret-key-keep-it-safe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    # Database (Aligned with Railway Defaults)
    DB_HOST: str = Field(default="localhost", alias="MYSQLHOST")
    DB_USER: str = Field(default="root", alias="MYSQLUSER")
    DB_PASSWORD: str = Field(default="", alias="MYSQLPASSWORD")
    DB_NAME: str = Field(default="breakdown_db", alias="MYSQLDATABASE")
    DB_PORT: int = Field(default=3306, alias="MYSQLPORT")

    # OpenAI
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        populate_by_name=True
    )

settings = Settings()
