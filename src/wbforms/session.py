from wbforms.datamodel.auth import WikibaseAuthorizationConfig
from wbforms.settings import get_settings
from wbforms.wikibase import Wikibase


class WikibaseSession(Wikibase):
    """
    Wikibase connection configured from the application settings.
    """

    def __init__(self, auth_config: WikibaseAuthorizationConfig | None = None):
        settings = get_settings()
        super().__init__(
            sparql_endpoint=settings.wikibase_sparql_endpoint,
            website=settings.wikibase_website,
            item_prefix=settings.wikibase_item_prefix,
            property_prefix=settings.wikibase_property_prefix,
            mediawiki_api_url=settings.wikibase_mediawiki_api_url,
            mediawiki_rest_url=settings.wikibase_mediawiki_rest_url,
            auth_config=auth_config,
        )
