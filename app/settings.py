from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_KEY: str
    BASE_URL: str
    W_ACTIVITY_ENDPOINT: str
    ADDRESS_1: str


settings = Settings()
