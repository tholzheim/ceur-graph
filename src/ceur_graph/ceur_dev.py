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
    def get_proceedings_by_volume_number_query(cls, volume_number: int) -> str | None:
        """
        Get the ceur-dev volume QID for the given volume number.
        :param volume_number: volume number
        :return: QID of the volume QID
        """
        query_str = files(ceur_graph.resources.queries).joinpath("ceur-dev_proceedings_by_volume_number.rq").read_text()
        query_template = Template(query_str)
        query = query_template.safe_substitute({"volume_number": volume_number})
        return query

    def get_proceedings_by_volume_number(self, volume_id: int) -> str | None:
        """
        Get the ceur-dev volume QID for the given volume id.
        :param volume_id: volume id
        :return:
        """
        query = self.get_proceedings_by_volume_number_query(volume_id)
        if query is None:
            logger.debug(f"Unable to get proceedings by volume number: {volume_id} as the query could not be generated")
            return None
        qres = self.execute_query(query, self.sparql_endpoint)
        if len(qres) == 0:
            return None
        elif len(qres) == 1:
            return qres[0].get("proceedings")
        else:
            logger.debug(f"Found {len(qres)} proceedings for volume {volume_id}")
            return qres[0].get("proceedings")
