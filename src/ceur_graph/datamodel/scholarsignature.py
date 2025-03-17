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


class ScholarSignatureBase(ExtractedStatement):
    scholar_id: Annotated[
        ItemStatementSubjectType,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/statement/P93",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = WikibaseSnakType.UNKNOWN_VALUE.value
    series_ordinal: Annotated[
        int,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P18",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            }
        ),
    ] = None  # type: ignore
    orcid_id: Annotated[
        str,
        Field(
            pattern=r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]",
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P87",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            },
        ),
    ] = None  # type: ignore
    affiliation_string: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P19",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            }
        ),
    ] = None  # type: ignore
    affiliation: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P20",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    dblp_author_id: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P88",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            },
        ),
    ] = None  # type: ignore


class ScholarSignatureCreate(ScholarSignatureBase):
    """
    Scholar signature model for creating a scholar signature
    """


ScholarSignatureUpdate: type = make_partial_model(ScholarSignatureCreate, "ScholarSignatureUpdate")


class ScholarSignature(ScholarSignatureBase, Statement):
    """
    Scholar signature model for proceedings and papers
    """
