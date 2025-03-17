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
from ceur_graph.datamodel.volume import Volume, VolumeCreate, VolumeUpdate

router = APIRouter(
    prefix="/volumes",
    tags=["Volumes"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Volume, status_code=status.HTTP_201_CREATED)
def create_volume(
    volume: Annotated[VolumeCreate, Body(embed=True)],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Create a new volume.
    """
    return handle_item_creation(
        wikibase=ceur_dev,
        model_obj=volume,
        target_model=Volume,
    )


@router.get("/{volume_id}", response_model=Volume, status_code=status.HTTP_200_OK)
async def get_volume(volume_id: str):
    """
    Get volume data by id.
    """
    return handle_get_item_by_id(
        wikibase=CeurDev(),
        item_id=volume_id,
        target_model=Volume,
    )


@router.put("/{volume_id}", response_model=Volume, status_code=status.HTTP_200_OK)
async def update_volume(
    volume_id: Annotated[str, Field(pattern=r"Q\d+")],
    volume: Annotated[VolumeUpdate, Body(embed=True)],  # type: ignore
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
):
    """
    Update volume data by id.
    """
    return handle_item_update(
        wikibase=ceur_dev,
        item_id=volume_id,
        model_obj=volume,
        target_model=Volume,
    )


@router.delete("/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volume(
    volume_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    reason: Annotated[str | None, Field(description="Reason for deletion")] = None,
):
    """
    Delete volume data by id.
    """
    return handle_item_deletion(
        wikibase=ceur_dev,
        item_id=volume_id,
        reason=reason,
        target_model=Volume,
    )
