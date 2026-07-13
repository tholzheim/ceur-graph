"""Application settings loaded from environment / .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the wbforms backend.

    All Wikibase URLs default to the ceur-dev instance so the service runs
    without any extra configuration. Override via environment variables
    (prefix ``WBFORMS_``) or a ``.env`` file to point at a different
    Wikibase deployment.
    """

    model_config = SettingsConfigDict(
        env_prefix="WBFORMS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # ToDo: Check where these constants are used
    wikibase_website: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/")
    wikibase_sparql_endpoint: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/query/sparql")
    wikibase_item_prefix: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/entity/")
    wikibase_property_prefix: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/prop/direct/")
    wikibase_mediawiki_api_url: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/w/api.php")
    wikibase_mediawiki_rest_url: HttpUrl = HttpUrl("https://ceur-dev.wikibase.cloud/w/rest.php")

    schema_path: Path = Path(__file__).parent / "schema" / "ceur_graph.yaml"

    oauth_version: Literal["1.0a", "2.0"] = "2.0"
    oauth_client_id: str | None = None
    oauth_client_secret: SecretStr | None = None
    oauth_redirect_uri: HttpUrl | None = None

    app_base_url: HttpUrl = HttpUrl("http://localhost:8000/")
    session_ttl_minutes: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
