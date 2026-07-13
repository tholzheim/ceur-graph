import logging

from wbforms.session import WikibaseSession

logger = logging.getLogger(__name__)


class CeurDev(WikibaseSession):
    """
    CEUR-WS use case: queries against the ceur-dev Wikibase instance.
    """

    @classmethod
    def get_papers_of_proceedings_by_volume_number_query(cls, volume_number: int) -> str:
        """
        Get the query to get papers of volume by volume number.
        :param volume_number: volume number
        :return: QID of the volume QID
        """
        return cls._load_query_and_substitute(
            query_file="ceur-dev_papers_of_proceedings_by_volume_number.rq", params={"volume_number": volume_number}
        )

    @classmethod
    def get_proceedings_by_volume_number_query(cls, volume_number: int) -> str:
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

    def get_papers_of_proceedings_by_volume_number(self, volume_id: int) -> list[str]:
        """
        Get the ceur-dev papers QID for the given volume id.
        :param volume_id: volume id
        :return:
        """
        query = self.get_papers_of_proceedings_by_volume_number_query(volume_id)
        qres = self.execute_query(query, self.sparql_endpoint)
        paper_ids = []
        for record in qres:
            document_qid = record.get("document")
            if document_qid is not None:
                paper_ids.append(document_qid)
        return paper_ids
