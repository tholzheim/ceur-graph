import logging
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from pydantic import Field
from starlette import status

from ceur_graph.api.auth import get_current_user

from ceur_graph.ceur_dev import CeurDev
from ceur_graph.api.utils import (
    handle_statement_deletion_by_id,
    handle_statement_creation,
    handle_statement_deletion_by_object,
    handle_statement_update,
    handle_get_all_statements,
)
from ceur_graph.datamodel.editorsignature import (
    EditorSignature,
    EditorSignatureCreate,
    EditorSignatureUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/volumes/{volume_id}/editors",
    tags=["EditorSignature"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[EditorSignature],
)
def get_editors(volume_id: Annotated[str, Field(pattern=r"Q\d+")]):
    """
    Get editors
    """
    return handle_get_all_statements(
        wikibase=CeurDev(),
        item_id=volume_id,
        target_model=EditorSignature,
    )


@router.post("/")
async def create_volume_editor(
    volume_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    scholar_signature: Annotated[EditorSignatureCreate, Body(embed=True)],
):
    return handle_statement_creation(
        wikibase=ceur_dev,
        item_id=volume_id,
        model_obj=scholar_signature,
        target_model=EditorSignature,
    )


@router.delete("/{statement_id}")
async def delete_volume_editor_by_statement_id(
    volume_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Delete subject by statement id
    """
    return handle_statement_deletion_by_id(
        wikibase=ceur_dev,
        item_id=volume_id,
        statement_id=statement_id,
        model=EditorSignature,
    )


@router.delete("/")
async def delete_volume_editor(
    volume_id: Annotated[str, Field(pattern=r"Q\d+")],
    object_named_as: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Delete subject by statement id
    """
    return handle_statement_deletion_by_object(
        wikibase=ceur_dev,
        item_id=volume_id,
        object_named_as=object_named_as,
        model=EditorSignature,
    )


@router.put(
    "/{statement_id}", response_model=EditorSignature, status_code=status.HTTP_200_OK
)
async def update_volume_editor(
    volume_id: Annotated[str, Field(pattern=r"Q\d+")],
    statement_id: str,
    scholar_signature: Annotated[EditorSignatureUpdate, Body(embed=True)], # type: ignore
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Update volume editor signature
    """
    return handle_statement_update(
        wikibase=ceur_dev,
        item_id=volume_id,
        statement_id=statement_id,
        model_obj=scholar_signature,
        target_model=EditorSignature,
    )
