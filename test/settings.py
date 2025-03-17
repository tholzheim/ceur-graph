from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")
    WIKIBASE_BOT_USERNAME: str = "user"
    WIKIBASE_BOT_PASSWORD: str = None
