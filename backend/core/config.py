from pydantic import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "your-super-secret-key"  # load from .env in prod
    JWT_ALGORITHM: str = "HS256"
    # Setting the expiry time as 10 mins to implement JIT and JET principles
    JWT_EXPIRY_MINUTES: int = 10
    DATABASE_URL: str = "sqlite:///./financial_app.db"
    SERVER_ID: str = "trusted_FinLLM_server_1975"

    class Config:
        env_file = ".env"

settings = Settings()
