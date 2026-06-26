from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MySQL
    MYSQL_URL : str

    # Admin
    ADMIN_SECRET : str

    # Default rate limit config
    DEFAULT_MAX_TOKENS:  int   = 10
    DEFAULT_REFILL_RATE: float = 2.0
    DEFAULT_WINDOW_SIZE: int   = 60
    DEFAULT_ALGORITHM:   str   = "token_bucket"

    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    CONFIG_CACHE_TTL: int = 60 # seconds

settings = Settings()
