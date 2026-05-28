"""Application settings loaded from environment / .env file."""

from functools import lru_cache

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the CEUR-Graph backend.

    All Wikibase URLs default to the ceur-dev instance so the service runs
    without any extra configuration. Override via environment variables
    (prefix ``CEUR_GRAPH_``) or a ``.env`` file to point at a different
    Wikibase deployment.
    """

    model_config = SettingsConfigDict(
        env_prefix="CEUR_GRAPH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    wikibase_website: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/")
    wikibase_sparql_endpoint: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/query/sparql")
    wikibase_item_prefix: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/entity/")
    wikibase_property_prefix: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/prop/direct/")
    wikibase_mediawiki_api_url: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/w/api.php")
    wikibase_mediawiki_rest_url: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/w/rest.php")

    oauth_client_id: str | None = "a72e72dd471cd7ac1d492c89d1cc153d"
    oauth_client_secret: SecretStr | None = "11c1d79dc6cca200bfb0dba7589afddbd4ad2ffa"
    oauth_redirect_uri: HttpUrl | None =  HttpUrl("http://localhost:8000/oauth/callback")

    app_base_url: HttpUrl = HttpUrl("http://localhost:8000/")
    session_ttl_minutes: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
