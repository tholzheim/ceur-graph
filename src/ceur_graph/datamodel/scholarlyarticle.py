from typing import Annotated

from pydantic import AnyHttpUrl, Field
from wikibaseintegrator import datatypes

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    ItemBase,
)
from ceur_graph.datamodel.paper import PaperBase
from ceur_graph.datamodel.utils import make_partial_model


class ScholarlyArticleBase(PaperBase):
    """
    ceur-ws ScholarlyArticle model for creating a ScholarlyArticle object
    """

    wikidata_id: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P2",
                WIKIBASE_TYPE: datatypes.ExternalID.DTYPE,
            }
        ),
    ]
    published_in: Annotated[
        str,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/direct/P94",
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


class ScholarlyArticleCreate(ScholarlyArticleBase):
    """
    ceur-ws ScholarlyArticle model for creating a new ScholarlyArticle object
    """


class ScholarlyArticle(ScholarlyArticleBase, ItemBase):
    """
    ceur-ws ScholarlyArticle model
    """


ScholarlyArticleUpdate = make_partial_model(ScholarlyArticleCreate, "ScholarlyArticleUpdate")
