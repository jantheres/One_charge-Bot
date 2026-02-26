from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "1Charge Chatbot"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "your-secret-key-keep-it-safe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    # Database (Bulletproof Railway + Standard Aliases)
    DB_HOST: str = Field(default="localhost", validation_alias=AliasChoices("MYSQLHOST", "DB_HOST", "DATABASE_HOST"))
    DB_USER: str = Field(default="root", validation_alias=AliasChoices("MYSQLUSER", "DB_USER", "DATABASE_USER"))
    DB_PASSWORD: str = Field(default="", validation_alias=AliasChoices("MYSQLPASSWORD", "MYSQL_ROOT_PASSWORD", "DB_PASSWORD", "DATABASE_PASSWORD"))
    DB_NAME: str = Field(default="breakdown_db", validation_alias=AliasChoices("MYSQLDATABASE", "MYSQL_DATABASE", "DB_NAME", "DATABASE_NAME"))
    DB_PORT: int = Field(default=3306, validation_alias=AliasChoices("MYSQLPORT", "DB_PORT", "DATABASE_PORT"))

    # OpenAI
    OPENAI_API_KEY: str = Field(default="", alias="OPENAI_API_KEY", validation_alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        populate_by_name=True
    )

settings = Settings()
