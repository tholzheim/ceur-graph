import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import Field
from starlette import status

from ceur_graph.api.auth import get_current_user
from ceur_graph.datamodel.reference import (
    ReferenceCreate,
    ReferenceUpdate,
    Reference,
)
from ceur_graph.ceur_dev import CeurDev
from ceur_graph.api.utils import (
    handle_statement_deletion_by_id,
    handle_statement_creation,
    handle_statement_update,
    handle_get_all_statements,
    handle_get_statement_by_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/papers/{paper_id}/references",
    tags=["References"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Reference])
def get_paper_references(paper_id: Annotated[str, Field(pattern=r"Q\d+")]):
    """
    Get paper references
    """
    return handle_get_all_statements(
        wikibase=CeurDev(),
        item_id=paper_id,
        target_model=Reference,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Reference)
def create_paper_reference(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    reference: ReferenceCreate,
):
    """
    Create paper references
    """
    return handle_statement_creation(
        wikibase=ceur_dev,
        item_id=paper_id,
        model_obj=reference,
        target_model=Reference,
    )


@router.get("/{statement_id}", status_code=status.HTTP_200_OK, response_model=Reference)
def get_paper_reference_by_statement_id(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Get paper reference by statement id
    """
    return handle_get_statement_by_id(
        wikibase=CeurDev(),
        item_id=paper_id,
        statement_id=statement_id,
        target_model=Reference,
    )


@router.put("/{statement_id}", status_code=status.HTTP_200_OK, response_model=Reference)
def update_paper_reference(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    reference: ReferenceUpdate,
):
    """
    Update paper reference
    """
    return handle_statement_update(
        wikibase=ceur_dev,
        item_id=paper_id,
        statement_id=statement_id,
        model_obj=reference,
        target_model=Reference,
    )


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper_reference(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Delete paper reference
    """
    return handle_statement_deletion_by_id(
        wikibase=ceur_dev,
        item_id=paper_id,
        statement_id=statement_id,
        model=Reference,
    )
