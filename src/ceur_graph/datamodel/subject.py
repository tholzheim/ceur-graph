from typing import Annotated

from pydantic import Field
from wikibaseintegrator import datatypes
from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    ExtractedStatement,
    ItemStatementSubjectType,
    Statement,
)
from ceur_graph.datamodel.utils import make_partial_model


class SubjectBase(ExtractedStatement):
    subject_id: Annotated[
        ItemStatementSubjectType,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/statement/P72",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = WikibaseSnakType.UNKNOWN_VALUE.value

    class Config:
        title = "Subject"


class SubjectCreate(SubjectBase):
    """
    Paper and proceedings subjects
    """


SubjectUpdate = make_partial_model(SubjectCreate, "PaperUpdate")


class Subject(SubjectBase, Statement):
    """
    Paper and proceedings subjects
    """
