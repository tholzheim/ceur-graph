from typing import Annotated

from pydantic import Field
from wikibaseintegrator import datatypes
from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    ItemStatementSubjectType,
    Statement,
    WIKIBASE_TYPE,
)
from ceur_graph.datamodel.scholarsignature import ScholarSignatureBase
from ceur_graph.datamodel.utils import make_partial_model


class EditorSignatureBase(ScholarSignatureBase):
    scholar_id: Annotated[
        ItemStatementSubjectType,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/statement/P10",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = WikibaseSnakType.UNKNOWN_VALUE.value


class EditorSignatureCreate(EditorSignatureBase):
    """
    Editor signature model for creating a scholar signature
    """


EditorSignatureUpdate = make_partial_model(
    EditorSignatureCreate, "EditorSignatureUpdate"
)


class EditorSignature(EditorSignatureBase, Statement):
    """
    Editor signature model for proceedings
    """
