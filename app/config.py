from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./gabin.db"
    frontend_url: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()
