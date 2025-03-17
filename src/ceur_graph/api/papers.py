import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends
from pydantic import Field
from starlette import status

from ceur_graph.api.auth import get_current_user
from ceur_graph.api.utils import (
    handle_get_item_by_id,
    handle_item_creation,
    handle_item_deletion,
    handle_item_update,
)
from ceur_graph.ceur_dev import CeurDev
from ceur_graph.datamodel.paper import Paper, PaperCreate, PaperUpdate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/papers",
    tags=["papers"],
    # dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Paper, status_code=status.HTTP_201_CREATED)
def create_paper(
    paper: Annotated[PaperCreate, Body(embed=True)],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    return handle_item_creation(
        wikibase=ceur_dev,
        model_obj=paper,
        target_model=Paper,
    )


@router.get("/{paper_id}", response_model=Paper, status_code=status.HTTP_200_OK)
async def get_paper(paper_id: str):
    return handle_get_item_by_id(
        wikibase=CeurDev(),
        item_id=paper_id,
        target_model=Paper,
    )


@router.put("/{paper_id}", response_model=Paper, status_code=status.HTTP_200_OK)
async def update_paper(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    paper: Annotated[PaperUpdate, Body(embed=True)],  # type: ignore
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    return handle_item_update(
        wikibase=ceur_dev,
        item_id=paper_id,
        model_obj=paper,
        target_model=Paper,
    )


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paper(
    paper_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    reason: Annotated[str | None, Field(description="Reason for deletion")] = None,
):
    return handle_item_deletion(
        wikibase=ceur_dev,
        item_id=paper_id,
        reason=reason,
        target_model=Paper,
    )
