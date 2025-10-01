from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "your-super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 10
    DATABASE_URL: str = "sqlite:///./financial_app.db"
    SERVER_ID: str = "trusted_FinLLM_server_1975"
    GOOGLE_GEMINI_API_KEY: str
    KEY_PASSPHRASE: str
    DB_ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
