from typing import Annotated

from pydantic import AnyHttpUrl, Field
from wikibaseintegrator import datatypes

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    WIKIDATA_ID,
    EntityBase,
    ItemBase,
)
from ceur_graph.datamodel.utils import make_partial_model


class PaperBase(EntityBase):
    """
    ceur-ws Paper model for creating a Paper object
    """

    published_in: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P94",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ]
    full_work_available_at_url: Annotated[
        AnyHttpUrl,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P12",
                WIKIBASE_TYPE: datatypes.URL.DTYPE,
            }
        ),
    ]
    title: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P5",
                WIKIDATA_ID: "http://www.wikidata.org/prop/direct/P1476",
                WIKIBASE_TYPE: datatypes.MonolingualText.DTYPE,
            }
        ),
    ] = None  # type: ignore
    pages: Annotated[
        int,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P89",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            },
        ),
    ] = None  # type: ignore
    dblp_publication_id: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P9",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None  # type: ignore
    copyright_license: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P96",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    presented_in: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P95",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    language_of_work: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P14",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    wikidata_id: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P2",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None  # type: ignore


class PaperCreate(PaperBase):
    """
    ceur-ws Paper model for creating a new Paper object
    """


class Paper(PaperBase, ItemBase):
    """
    ceur-ws Paper model
    """


PaperUpdate = make_partial_model(PaperCreate, "PaperUpdate")
