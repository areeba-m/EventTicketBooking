from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "event_ticket_booking"
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXP_MINUTES: int = 30


settings = Settings()
