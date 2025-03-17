from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, constr, model_validator
from pydantic.fields import FieldInfo
from wikibaseintegrator import datatypes
from wikibaseintegrator.wbi_enums import WikibaseSnakType

WIKIBASE_TYPE = "wikibase_type"
CEUR_DEV_ID = "CEUR_DEV_ID"
WIKIDATA_ID = "WIKIDATA_ID"


class ItemBase(BaseModel):
    """
    Wikibase item model
    """

    qid: Annotated[
        str | None,
        Field(
            description="Qid of the paper",
            pattern=r"Q\d+",
            json_schema_extra={CEUR_DEV_ID: "rdf:subject"},
        ),
    ]


class EntityBase(BaseModel):
    label: Annotated[str, Field(json_schema_extra={CEUR_DEV_ID: "rdfs:label"})]
    description: Annotated[str, Field(json_schema_extra={CEUR_DEV_ID: "schema:description"})]


class StatementBase(BaseModel):
    @classmethod
    def get_statement_subject(cls, lookup_key: str) -> str:
        """
        Each statement is expected to have one field as the statement subject.
        :return:
        """
        field_name: str
        field_metadata: FieldInfo
        subject_field = None
        for field_name, field_metadata in cls.model_fields.items():
            field_prop_id = field_metadata.json_schema_extra.get(lookup_key)
            if field_prop_id is not None:
                id_parts = field_prop_id.split("/")
                if len(id_parts) > 2 and id_parts[-2] == "statement":
                    subject_field = field_name
                    break
        if subject_field is None:
            raise Exception(f"Model {cls.__name__} has no statement object defined for {lookup_key}")
        return subject_field

    @classmethod
    def get_qualifier_fields(cls, lookup_key: str) -> list[str]:
        """
        Get fields that are stored as statement qualifier
        :param lookup_key:
        :return:
        """
        field_name: str
        field_metadata: FieldInfo
        qualifier_fields: list[str] = []
        for field_name, field_metadata in cls.model_fields.items():
            field_prop_id = field_metadata.json_schema_extra.get(lookup_key)
            if field_prop_id is not None:
                id_parts = field_prop_id.split("/")
                if len(id_parts) > 2 and id_parts[-2] == "qualifier":
                    qualifier_fields.append(field_name)
        return qualifier_fields


class Statement(StatementBase):
    statement_id: Annotated[str, Field(pattern=r"Q\d+", json_schema_extra={CEUR_DEV_ID: "rdf:subject"})]


class ExtractedStatement(StatementBase):
    """
    Statement which is extracted and thus has the object named as qualifier set
    The extracted value field is optional to be compatible to already existing entries
    """

    object_named_as: Annotated[
        str | None,
        Field(
            json_schema_extra={
                CEUR_DEV_ID: "https://ceur-dev.wikibase.cloud/prop/qualifier/P91",
                WIKIBASE_TYPE: datatypes.String.DTYPE,
            }
        ),
    ] = None

    @model_validator(mode="after")
    def validate_object_named_as(self) -> Self:
        """
        Check if the object_named_as field must be set
        """
        statement_object_field = self.get_statement_subject(CEUR_DEV_ID)
        statement_object_value = getattr(self, statement_object_field)
        if statement_object_value == WikibaseSnakType.UNKNOWN_VALUE.value and self.object_named_as is None:
            raise ValueError(
                f"If the statement object field {statement_object_field} is set as unknown value the object_named_as "
                f"field must be set."
            )
        return self

    def __eq__(self, other):
        other_object_named_as = getattr(other, "object_named_as", None)
        if None in [self.object_named_as, other_object_named_as]:
            stmt_object_field = self.get_statement_subject(CEUR_DEV_ID)
            return getattr(self, stmt_object_field) == getattr(other, stmt_object_field)
        else:
            return self.object_named_as == other_object_named_as


ItemStatementSubjectType = Literal["somevalue"] | constr(pattern=r"^Q\d+$")


class Coordinate(BaseModel):
    longitude: float
    latitude: float
