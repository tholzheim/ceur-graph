import logging
from importlib.resources import files
from string import Template

import ceur_graph.resources.queries
from ceur_graph.datamodel.auth import WikibaseAuthorizationConfig
from ceur_graph.wikibase import Wikibase

logger = logging.getLogger(__name__)


class CeurDev(Wikibase):
    """
    Provides access to the Ceur-dev Wikibase API.
    """

    def __init__(self, auth_config: WikibaseAuthorizationConfig | None = None):
        super().__init__(
            sparql_endpoint="https://ceur-dev.wikibase.cloud/query/sparql",
            website="https://ceur-dev.wikibase.cloud/",
            item_prefix="https://ceur-dev.wikibase.cloud/entity/",
            property_prefix="https://ceur-dev.wikibase.cloud/prop/direct/",
            mediawiki_api_url="https://ceur-dev.wikibase.cloud/w/api.php",
            auth_config=auth_config,
        )

    @classmethod
    def _load_query_and_substitute(cls, query_file: str, params: dict) -> str | None:
        """
        Load the query file and substitute it with the provided params.
        :param query_file:
        :param params:
        :return:
        """
        query_str = files(ceur_graph.resources.queries).joinpath(query_file).read_text()
        query_template = Template(query_str)
        query = query_template.safe_substitute(params)
        if query is None:
            logger.debug(f"Unable to build query: {query_file} with params: {params}")
            return None
        return query

    @classmethod
    def get_papers_of_proceedings_by_volume_number_query(cls, volume_number: int) -> str | None:
        """
        Get the query to get papers of volume by volume number.
        :param volume_number: volume number
        :return: QID of the volume QID
        """
        return cls._load_query_and_substitute(
            query_file="ceur-dev_papers_of_proceedings_by_volume_number.rq", params={"volume_number": volume_number}
        )

    @classmethod
    def get_proceedings_by_volume_number_query(cls, volume_number: int) -> str | None:
        """
        Get the ceur-dev volume QID for the given volume number.
        :param volume_number: volume number
        :return: QID of the volume QID
        """
        return cls._load_query_and_substitute(
            query_file="ceur-dev_proceedings_by_volume_number.rq", params={"volume_number": volume_number}
        )

    def get_proceedings_by_volume_number(self, volume_id: int) -> str | None:
        """
        Get the ceur-dev volume QID for the given volume id.
        :param volume_id: volume id
        :return:
        """
        query = self.get_proceedings_by_volume_number_query(volume_id)

        qres = self.execute_query(query, self.sparql_endpoint)
        if len(qres) == 0:
            return None
        elif len(qres) == 1:
            return qres[0].get("proceedings")
        else:
            logger.debug(f"Found {len(qres)} proceedings for volume {volume_id}")
            return qres[0].get("proceedings")

    def get_papers_of_proceedings_by_volume_number(self, volume_id: int) -> list[str] | None:
        """
        Get the ceur-dev papers QID for the given volume id.
        :param volume_id: volume id
        :return:
        """
        query = self.get_papers_of_proceedings_by_volume_number_query(volume_id)
        qres = self.execute_query(query, self.sparql_endpoint)
        papers = [record.get("document") for record in qres]
        return papers
