from typing import Annotated

from pydantic import AnyHttpUrl, Field

from wikibaseintegrator import datatypes

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    EntityBase,
    ItemBase,
    WIKIBASE_TYPE,
    WIKIDATA_ID,
)
from ceur_graph.datamodel.utils import make_partial_model


class VolumeBase(EntityBase):
    """
    ceur-ws volume model
    """

    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P5",
                WIKIDATA_ID: "http://www.wikidata.org/prop/direct/P1476",
                WIKIBASE_TYPE: datatypes.MonolingualText.DTYPE,
            }
        ),
    ] = None
    short_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P11",
                WIKIBASE_TYPE: datatypes.MonolingualText.DTYPE,
            }
        ),
    ] = None
    dblp_publication_id: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P9",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None
    copyright_license: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P96",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None
    wikidata_id: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P2",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None
    language_of_work: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P14",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None
    urn: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P7",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None
    is_proceedings_from: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P16",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None
    full_work_available_at_url: Annotated[
        AnyHttpUrl | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P12",
                WIKIBASE_TYPE: datatypes.URL.DTYPE,
            }
        ),
    ] = None
    volume: Annotated[
        int | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P17",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            },
        ),
    ] = None
    part_of_the_series: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P15",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None


class VolumeCreate(VolumeBase):
    """
    ceur-ws volume model for creating a bew item
    """


VolumeUpdate = make_partial_model(VolumeCreate, "VolumeUpdate")


class Volume(VolumeBase, ItemBase):
    """
    ceur-ws volume model
    """
