import logging

from fastapi import APIRouter

from ceur_graph.ceur_dev import CeurDev

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ceur-ws",
    tags=["IDs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/Vol-{volume_number}/papers")
def get_volume_paper_ids(volume_number: int):
    """
    Get the documents published in a proceedings by its volume number.
    The document can either be a paper, preface, invited paper or keynote.
    """
    volume_documents = CeurDev().get_papers_of_proceedings_by_volume_number(volume_number)
    return volume_documents


@router.get("/Vol-{volume_number}")
def get_volume_id(volume_number: int):
    """
    Get the Qid of the volume with the given volume number.
    """
    proceedings_qid = CeurDev().get_proceedings_by_volume_number(volume_number)
    return proceedings_qid
