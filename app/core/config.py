from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Mid Project"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret_key_1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SYNC_DATABASE_URL: str = "sqlite:///./test.db"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:4321"]
    AWS_REGION: str = "ap-south-2"
    AWS_ACCESS_KEY_ID: str = "key-id-here"
    AWS_SECRET_ACCESS_KEY: str = "acces-key-here"
    CF_ZONE_ID: str = "zone-id-here"
    CF_API_TOKEN: str = "token-here"
    VPS_PUBLIC_IP: str = "ip-here"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
