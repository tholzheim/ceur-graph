import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import Field
from starlette import status

from ceur_graph.api.auth import get_current_user
from ceur_graph.datamodel.subject import (
    Subject,
    SubjectBase,
    SubjectCreate,
    SubjectUpdate,
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
    prefix="/papers/{paper_id}/subjects",
    tags=["Paper Subjects"],
    # dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Subject])
def get_subjects(paper_id: Annotated[str, Field(pattern=r"Q\d+")]):
    """
    Get paper subjects
    """
    return handle_get_all_statements(
        wikibase=CeurDev(),
        item_id=paper_id,
        target_model=Subject,
    )


@router.post("/", status_code=status.HTTP_200_OK, response_model=Subject)
def create_subject(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    subject: SubjectCreate,
):
    """
    Create paper subject
    """
    return handle_statement_creation(
        wikibase=ceur_dev,
        item_id=paper_id,
        model_obj=subject,
        target_model=Subject,
    )


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_by_statement_id(
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
        model=Subject,
    )


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_by_object_named_as(
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
        model=SubjectBase,
    )


@router.put("/{statement_id}", status_code=status.HTTP_200_OK, response_model=Subject)
def update_subject(
    paper_id: Annotated[str, Field(pattern=r"Q\d+")],
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    subject: SubjectUpdate,# type: ignore
    statement_id: str,
):
    """
    Update subject by statement id
    """
    return handle_statement_update(
        wikibase=ceur_dev,
        item_id=paper_id,
        statement_id=statement_id,
        model_obj=subject,
        target_model=Subject,
    )
