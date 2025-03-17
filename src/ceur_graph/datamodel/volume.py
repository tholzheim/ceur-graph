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


class VolumeBase(EntityBase):
    """
    ceur-ws volume model
    """

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
    short_name: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P11",
                WIKIBASE_TYPE: datatypes.MonolingualText.DTYPE,
            }
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
    wikidata_id: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P2",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
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
    urn: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P7",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ] = None  # type: ignore
    is_proceedings_from: Annotated[
        list[str],
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P16",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore
    full_work_available_at_url: Annotated[
        AnyHttpUrl,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P12",
                WIKIBASE_TYPE: datatypes.URL.DTYPE,
            }
        ),
    ] = None  # type: ignore
    volume: Annotated[
        int,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P17",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            },
        ),
    ] = None  # type: ignore
    part_of_the_series: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P15",
                WIKIBASE_TYPE: datatypes.Item.DTYPE,
            }
        ),
    ] = None  # type: ignore


class VolumeCreate(VolumeBase):
    """
    ceur-ws volume model for creating a bew item
    """


VolumeUpdate = make_partial_model(VolumeCreate, "VolumeUpdate")


class Volume(VolumeBase, ItemBase):
    """
    ceur-ws volume model
    """
