import logging
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from pydantic import Field
from starlette import status

from ceur_graph.api.auth import get_current_user
from ceur_graph.datamodel.scholarsignature import (
    ScholarSignature,
    ScholarSignatureCreate,
    ScholarSignatureUpdate,
)
from ceur_graph.ceur_dev import CeurDev
from ceur_graph.api.utils import (
    handle_statement_deletion_by_id,
    handle_statement_creation,
    handle_statement_deletion_by_object,
    handle_statement_update,
    handle_get_all_statements,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/papers/{paper_id}/authors",
    tags=["AuthorSignature"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ScholarSignature],
)
def get_authors(paper_id: Annotated[str, Field(pattern=r"Q\d+")]):
    """
    Get authors
    """
    return handle_get_all_statements(
        wikibase=CeurDev(),
        item_id=paper_id,
        target_model=ScholarSignature,
    )


@router.post("/")
async def create_paper_author(
    paper_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    scholar_signature: Annotated[ScholarSignatureCreate, Body(embed=True)],
):
    return handle_statement_creation(
        wikibase=ceur_dev,
        item_id=paper_id,
        model_obj=scholar_signature,
        target_model=ScholarSignature,
    )


@router.delete("/{statement_id}")
async def delete_paper_author_by_statement_id(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Delete subject by statement id
    """
    return handle_statement_deletion_by_id(
        wikibase=ceur_dev,
        item_id=paper_id,
        statement_id=statement_id,
        model=ScholarSignature,
    )


@router.delete("/")
async def delete_paper_author(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    object_named_as: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Delete subject by statement id
    """
    return handle_statement_deletion_by_object(
        wikibase=ceur_dev,
        item_id=paper_id,
        object_named_as=object_named_as,
        model=ScholarSignature,
    )


@router.put(
    "/{statement_id}", response_model=ScholarSignature, status_code=status.HTTP_200_OK
)
async def update_paper_author(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    scholar_signature: Annotated[ScholarSignatureUpdate, Body(embed=True)],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Update paper author signature
    """
    return handle_statement_update(
        wikibase=ceur_dev,
        item_id=paper_id,
        statement_id=statement_id,
        model_obj=scholar_signature,
        target_model=ScholarSignature,
    )
