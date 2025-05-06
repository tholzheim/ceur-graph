import logging
from typing import Any, TypeVar, get_origin

from pydantic import AnyHttpUrl, BaseModel
from pydantic.fields import FieldInfo
from wikibaseintegrator import WikibaseIntegrator, datatypes
from wikibaseintegrator.datatypes import BaseDataType
from wikibaseintegrator.entities import ItemEntity
from wikibaseintegrator.models import Claim, Snak
from wikibaseintegrator.wbi_enums import ActionIfExists, WikibaseSnakType

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    Coordinate,
    ExtractedStatement,
    Statement,
    StatementBase,
)
from ceur_graph.wikibase import Wikibase

logger = logging.getLogger(__name__)


def create_item_from_model(model: BaseModel, wbi: WikibaseIntegrator) -> ItemEntity:
    """
    Create ItemEntity from given object model
    :param model:
    :return:
    """
    item: ItemEntity = wbi.item.new()
    default_language = "en"

    field_name: str
    field_metadata: FieldInfo
    for field_name, field_metadata in model.model_fields.items():
        field_value = getattr(model, field_name)
        field_type = field_metadata.json_schema_extra.get(WIKIBASE_TYPE)
        field_prop_id = field_metadata.json_schema_extra.get(CEUR_DEV_ID)
        if field_prop_id == "rdfs:label":
            item.labels.set(default_language, field_value)
        elif field_prop_id == "schema:description":
            item.descriptions.set(default_language, field_value)
        else:
            # ToDo: Add support for qualifiers e.g. if value is an object and id has prefix p:
            claims = []
            if isinstance(field_value, list):
                values = field_value
            else:
                values = [field_value]
            for value in values:
                claim = get_claim(
                    prop_id=field_prop_id,
                    datatype=field_type,
                    value=value,
                    language=default_language,
                )
                if claim is not None:
                    claims.append(claim)
            for claim in claims:
                item.claims.add(claim)
    return item


def update_item_from_model(model: BaseModel, item: ItemEntity):
    """
    Update ItemEntity from given object model
    :param model:
    :param item:
    :param wbi:
    :return:
    """
    default_language = "en"
    for field_name in model.model_fields_set:
        field_value: Any = getattr(model, field_name)
        field_metadata: FieldInfo = model.model_fields.get(field_name)
        field_type = field_metadata.json_schema_extra.get(WIKIBASE_TYPE)
        field_prop_id = field_metadata.json_schema_extra.get(CEUR_DEV_ID)
        if field_prop_id == "rdfs:label":
            item.labels.set(
                default_language,
                field_value,
                action_if_exists=ActionIfExists.REPLACE_ALL,
            )
        elif field_prop_id == "schema:description":
            item.descriptions.set(
                default_language,
                field_value,
                action_if_exists=ActionIfExists.REPLACE_ALL,
            )
        else:
            # ToDo: Add support for qualifiers e.g. if value is an object and id has prefix p:
            claims = []
            if isinstance(field_value, list):
                values = field_value
            else:
                values = [field_value]
            for value in values:
                claim = get_claim(
                    prop_id=field_prop_id,
                    datatype=field_type,
                    value=value,
                    language=default_language,
                )
                if claim is not None:
                    claims.append(claim)
            if claims:
                item.claims.remove(field_prop_id)
                item.claims.add(claims)


def get_claim(prop_id: str, datatype: str, value: Any, language: str | None = None) -> Claim | None:
    """
    Get claim
    :param prop_id:
    :param datatype:
    :param value:
    :param language:
    :return:
    """
    if language is None:
        language = "en"
    if value is None:
        return None
    prop_nr = Wikibase.get_entity_id(prop_id)
    claim = None
    match datatype:
        case datatypes.MonolingualText.DTYPE:
            claim = datatypes.MonolingualText(language=language, text=value, prop_nr=prop_nr)
        case datatypes.Item.DTYPE:
            claim = datatypes.Item(value=value, prop_nr=prop_nr)
        case datatypes.URL.DTYPE:
            if isinstance(value, AnyHttpUrl):
                value = str(value)
            claim = datatypes.URL(value=value, prop_nr=prop_nr)
        case datatypes.String.DTYPE:
            claim = datatypes.String(value=str(value), prop_nr=prop_nr)
        case datatypes.Time.DTYPE:
            claim = datatypes.Time(value=value, prop_nr=prop_nr)
        case datatypes.ExternalID.DTYPE:
            claim = datatypes.ExternalID(value=value, prop_nr=prop_nr)
        case datatypes.GlobeCoordinate.DTYPE:
            if isinstance(value, Coordinate):
                claim = datatypes.GlobeCoordinate(longitude=value.longitude, latitude=value.latitude, prop_nr=prop_nr)
            else:
                logger.debug("Value is not a Coordinate object → ignoring in claim creation")
    return claim


def get_snak_value(snak: Snak) -> Any:
    value = None
    match snak.datatype:
        case datatypes.MonolingualText.DTYPE:
            value = snak.datavalue["value"]["text"]
        case datatypes.Item.DTYPE:
            value = snak.datavalue["value"]["id"]
        case datatypes.URL.DTYPE:
            value = snak.datavalue["value"]
        case datatypes.ExternalID.DTYPE:
            value = snak.datavalue["value"]
        case datatypes.String.DTYPE:
            value = snak.datavalue["value"]
        case datatypes.Time.DTYPE:
            value = snak.datavalue["value"].get("time")
    return value


def get_model_from_item(item: ItemEntity, model: type[BaseModel]) -> BaseModel:
    """
    Get model from given item entity
    :param item:
    :param model:
    :return:
    """
    default_language = "en"
    field_name: str
    field_metadata: FieldInfo
    record = {}
    for field_name, field_metadata in model.model_fields.items():
        # field_type = field_metadata.json_schema_extra.get(WIKIBASE_TYPE)
        field_prop_id = field_metadata.json_schema_extra.get(CEUR_DEV_ID)
        field_value = None
        if field_prop_id == "rdf:subject":
            field_value = item.id
        elif field_prop_id == "rdfs:label":
            label = item.labels.get(default_language)
            if label is not None:
                field_value = label.value
        elif field_prop_id == "schema:description":
            description = item.descriptions.get(default_language)
            if description is not None:
                field_value = description.value
        else:
            prop_nr = Wikibase.get_entity_id(field_prop_id)
            claims: list[Claim] = item.claims.get(prop_nr)
            if get_origin(field_metadata.annotation) is list:
                values = [get_snak_value(claim.mainsnak) for claim in claims]
                values = [value for value in values if value is not None]
                field_value = values
            else:
                claim = claims[0] if claims else None
                if claim is not None:
                    field_value = get_snak_value(claim.mainsnak)
        record[field_name] = field_value
    return model.model_validate(record)


T = TypeVar("T", bound=StatementBase)


def get_models_from_qualified_statement(item: ItemEntity, model: type[T]) -> list[T]:
    """
    Get list of qualified statement objects from given item entity
    ToDo: Report failed model creations and return the successful once along with the list of failure ids
    :param item:
    :param model:
    :return:
    """
    subject_field = model.get_statement_subject(CEUR_DEV_ID)
    subject_prop_id = model.model_fields.get(subject_field).json_schema_extra.get(CEUR_DEV_ID)
    subject_prop_nr = Wikibase.get_entity_id(subject_prop_id)
    claims: list[Claim] = item.claims.get(subject_prop_nr)
    statements: list[StatementBase] = []
    for claim in claims:
        model_obj = get_model_from_qualified_statement(claim, model)
        if model_obj is not None:
            statements.append(model_obj)
    return statements


def get_model_from_qualified_statement(claim: Claim, model: type[StatementBase]) -> StatementBase | None:
    """
    Get model from given claim entity
    :param claim:
    :param model:
    :return:
    """
    record = {}
    subject_field = model.get_statement_subject(CEUR_DEV_ID)
    if claim.mainsnak.snaktype is WikibaseSnakType.UNKNOWN_VALUE:
        record[subject_field] = WikibaseSnakType.UNKNOWN_VALUE.value
    elif claim.mainsnak.snaktype is WikibaseSnakType.NO_VALUE:
        return None
    else:
        record[subject_field] = get_snak_value(claim.mainsnak)
    if issubclass(model, Statement):
        record["statement_id"] = claim.id
    qualifier_fields = model.get_qualifier_fields(CEUR_DEV_ID)
    for qualifier_field in qualifier_fields:
        field_metadata: FieldInfo = model.model_fields.get(qualifier_field)
        field_prop_id = field_metadata.json_schema_extra.get(CEUR_DEV_ID)
        field_prop_nr = Wikibase.get_entity_id(field_prop_id)
        if field_prop_nr is None:
            continue
        else:
            qualifier: list[Snak] = claim.qualifiers.get(field_prop_nr)
            if qualifier is None or len(qualifier) == 0:
                continue
            elif get_origin(field_metadata.annotation) is list:
                values = [get_snak_value(snak) for snak in qualifier]
                record[qualifier_field] = values
            else:
                if len(qualifier) > 1:
                    logger.debug(
                        f"Statement {claim.id} has multiple qualifier values for {field_prop_nr} but the model only "
                        f"supports one value"
                    )
                record[qualifier_field] = get_snak_value(qualifier[0])
    model_obj = model.model_validate(record)
    return model_obj


def add_statement_from_model(item: ItemEntity, model: StatementBase):
    """
    Add model as statement to given item
    :param item:
    :param model:
    :return:
    """
    existing_statement = get_item_statement_by_model(item, model)
    if existing_statement is not None:
        raise ValueError(f"Statement already exists ({existing_statement}) ")
    claim = create_qualified_statement_from_model(model)
    item.claims.add(claim, action_if_exists=ActionIfExists.FORCE_APPEND)


def get_item_statement_by_model(
    item: ItemEntity,
    model: StatementBase,
    target_model: type[StatementBase | Statement] | None = None,
) -> StatementBase | Statement | None:
    """
    Get statement id from given item or None if the model is not a claim of the item
    :param target_model:
    :param item:
    :param model:
    :return:
    """
    if target_model is None:
        target_model = model.__class__
    statements = get_models_from_qualified_statement(item, target_model)
    for statement in statements:
        if statement == model:
            return statement
    return None


def get_item_statement_by_id(item: ItemEntity, statement_id: str, target_model: type[Statement]) -> Statement | None:
    """
    Get model object by statement_id from given item or None if the model is not a claim of the item
    :param item:
    :param statement_id:
    :param target_model:
    :return:
    """
    statements = get_models_from_qualified_statement(item, target_model)
    for statement in statements:
        if statement.statement_id == statement_id:
            return statement
    return None


def create_qualified_statement_from_model(model: StatementBase) -> Claim:
    subject_field = model.get_statement_subject(CEUR_DEV_ID)
    subject_prop_id = model.model_fields.get(subject_field).json_schema_extra.get(CEUR_DEV_ID)
    subject_prop_nr = Wikibase.get_entity_id(subject_prop_id)
    claim: Claim
    print(getattr(model, subject_field))
    if getattr(model, subject_field) == WikibaseSnakType.UNKNOWN_VALUE.value:
        claim = BaseDataType(prop_nr=subject_prop_nr, snaktype=WikibaseSnakType.UNKNOWN_VALUE)
    else:
        claim = get_claim(
            prop_id=subject_prop_nr,
            datatype=model.model_fields.get(subject_field).json_schema_extra.get(WIKIBASE_TYPE),
            value=getattr(model, subject_field),
        )
    add_qualifier_values_to_statement(claim, model)
    return claim


def add_qualifier_values_to_statement(claim: Claim, model: StatementBase):
    """
    Add the qualifier values of the given model to the given claim
    :param claim:
    :param model:
    :return:
    """
    qualifier_fields = model.get_qualifier_fields(CEUR_DEV_ID)
    for qualifier_field in qualifier_fields:
        qualifier_metadata: FieldInfo = model.model_fields.get(qualifier_field)
        qualifier_prop_id = qualifier_metadata.json_schema_extra.get(CEUR_DEV_ID)
        qualifier_type = qualifier_metadata.json_schema_extra.get(WIKIBASE_TYPE)
        qualifier_prop_nr = Wikibase.get_entity_id(qualifier_prop_id)
        qualifiers = []
        if qualifier_prop_nr is None or getattr(model, qualifier_field) is None:
            continue
        elif isinstance(getattr(model, qualifier_field), list):
            qualifier_values = getattr(model, qualifier_field)
        else:
            qualifier_values = [getattr(model, qualifier_field)]
        for value in qualifier_values:
            qualifier = get_claim(prop_id=qualifier_prop_nr, datatype=qualifier_type, value=value)
            qualifiers.append(qualifier)
        for snak in qualifiers:
            if snak is not None:
                claim.qualifiers.add(snak, action_if_exists=ActionIfExists.FORCE_APPEND)


def delete_property_statement_by_id(item: ItemEntity, statement_id: str, model_type: type[Statement]) -> bool:
    """
    Delete statement from given item
    :param item:
    :param statement_id:
    :param model_type:
    :return: True if the statement was deleted otherwise False if the statement was not found
    """
    subject_field = model_type.get_statement_subject(CEUR_DEV_ID)
    subject_prop_id = model_type.model_fields.get(subject_field).json_schema_extra.get(CEUR_DEV_ID)
    subject_prop_nr = Wikibase.get_entity_id(subject_prop_id)
    for claim in item.claims.get(subject_prop_nr):
        if claim.id == statement_id:
            claim.remove()
            return True
    return False


def delete_statement_by_matching_model(item: ItemEntity, model: StatementBase) -> bool:
    """
    Delete statement that matches given model
    :param item:
    :param model:
    :return:
    """
    subject_field = model.get_statement_subject(CEUR_DEV_ID)
    subject_prop_id = model.model_fields.get(subject_field).json_schema_extra.get(CEUR_DEV_ID)
    subject_prop_nr = Wikibase.get_entity_id(subject_prop_id)
    for claim in item.claims.get(subject_prop_nr):
        claim_model = get_model_from_qualified_statement(claim, model.__class__)
        if claim_model == model:
            claim.remove()
            return True
    return False


def get_calim_by_statement_id(item: ItemEntity, statement_id: str) -> Claim | None:
    """
    Get claim from given statement id
    :param item:
    :param statement_id:
    :return:
    """
    for claim in item.claims:
        if claim.id == statement_id:
            return claim
    return None


def update_qualified_statement_from_model(item: ItemEntity, statement_id: str, model: StatementBase):
    """
    Update the statement with the given model
    :param statement_id:
    :param item:
    :param model:
    :return:
    """
    claim = get_calim_by_statement_id(item, statement_id)
    if claim is None:
        raise ValueError("Statement not found")
    statement_object_field = model.get_statement_subject(CEUR_DEV_ID)
    statement_object_value = getattr(model, statement_object_field)
    statement_metadata = model.model_fields.get(statement_object_field)
    statement_prop_id = statement_metadata.json_schema_extra.get(CEUR_DEV_ID)
    statement_prop_nr = Wikibase.get_entity_id(statement_prop_id)
    statement_type = statement_metadata.json_schema_extra.get(WIKIBASE_TYPE)
    if statement_object_value is not None:
        if (
            issubclass(model.__class__, ExtractedStatement)
            and statement_object_value == WikibaseSnakType.UNKNOWN_VALUE.value
        ):
            new_mainsnak = BaseDataType(prop_nr=statement_prop_nr, snaktype=WikibaseSnakType.UNKNOWN_VALUE)
        else:
            new_mainsnak = get_claim(
                prop_id=statement_prop_id,
                datatype=statement_type,
                value=statement_object_value,
            )
        claim.mainsnak = new_mainsnak.mainsnak
    qualifier_fields = model.get_qualifier_fields(CEUR_DEV_ID)
    for model_field in model.model_fields_set:
        if model_field not in qualifier_fields:
            continue
        qualifier_metadata = model.model_fields.get(model_field)
        qualifier_prop_id = qualifier_metadata.json_schema_extra.get(CEUR_DEV_ID)
        qualifier_prop_nr = Wikibase.get_entity_id(qualifier_prop_id)
        # remove existing values
        for qualifier_snak in claim.qualifiers.get(qualifier_prop_nr):
            claim.qualifiers.remove(qualifier_snak)
    add_qualifier_values_to_statement(claim, model)
