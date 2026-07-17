from importlib.resources import files
from string import Template

import wbforms.resources.queries
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

    @classmethod
    def _load_query_and_substitute(cls, query_file: str, params: dict) -> str:
        """
        Load the query file and substitute it with the provided params.
        :param query_file:
        :param params:
        :return:
        """
        query_str = files(wbforms.resources.queries).joinpath(query_file).read_text()
        query_template = Template(query_str)
        query = query_template.safe_substitute(params)
        if query is None:
            raise ValueError(f"Unable to build query: {query_file} with params: {params}")
        return query
