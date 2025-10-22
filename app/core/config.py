from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Mid Project"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret_key_1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SYNC_DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"


settings = Settings()
