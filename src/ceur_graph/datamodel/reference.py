from typing import Annotated

from pydantic import AnyHttpUrl, Field
from wikibaseintegrator import datatypes
from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    WIKIDATA_ID,
    ExtractedStatement,
    ItemStatementSubjectType,
    Statement,
)
from ceur_graph.datamodel.utils import make_partial_model


class ReferenceBase(ExtractedStatement):
    """
    paper reference signature
    """

    reference_id: Annotated[
        ItemStatementSubjectType,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/statement/P90",
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
    doi: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P29",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None  # type: ignore
    title: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P5",
                WIKIDATA_ID: "http://www.wikidata.org/prop/qualifier/P1476",
                WIKIBASE_TYPE: datatypes.MonolingualText.DTYPE,
            }
        ),
    ] = None  # type: ignore
    author_name_string: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P92",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            }
        ),
    ] = None  # type: ignore
    author: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P93",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    described_at_url: Annotated[
        AnyHttpUrl,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P8",
                WIKIBASE_TYPE: datatypes.URL.DTYPE,
            }
        ),
    ] = None  # type: ignore


class ReferenceCreate(ReferenceBase):
    """
    paper reference model for creating the reference
    """


ReferenceUpdate = make_partial_model(ReferenceCreate, "ReferenceUpdate")


class Reference(ReferenceBase, Statement):
    """
    Paper reference model
    """
