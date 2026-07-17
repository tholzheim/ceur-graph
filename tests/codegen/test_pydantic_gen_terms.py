"""Tests for declarable label/description term slots (schema-controlled requiredness)."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from wikibaseintegrator import WikibaseIntegrator

from wbforms.api.frontend import _build_entity_schema
from wbforms.codegen.pydantic_gen import generate_models
from wbforms.datamodel.item import WIKIBASE_ID
from wbforms.wbgenerator import get_model_from_item

_BOILERPLATE = """
id: https://example.org/schema/test-terms
name: test_terms
description: Test schema for label/description term slots

prefixes:
  linkml: https://w3id.org/linkml/

default_range: string

imports:
  - linkml:types
"""

_SCHEMA = (
    _BOILERPLATE
    + """
slots:
  note:
    range: string
    annotations:
      wikibase_id: "https://example.org/prop/direct/P1"
      wikibase_type: string
  label:
    range: string
    required: false
  description:
    range: string
    required: false
    description: May be absent on existing items

classes:
  Plain:
    annotations:
      python_base: entity_item
    slots:
      - note

  OptionalDescription:
    annotations:
      python_base: entity_item
    slots:
      - description
      - note

  OptionalBoth:
    annotations:
      python_base: entity_item
    slots:
      - label
      - description
      - note

  RequiredAgain:
    annotations:
      python_base: entity_item
    slots:
      - description
      - note
    slot_usage:
      description:
        required: true
"""
)


def _generate(tmp_path: Path, schema_yaml: str) -> dict[str, type]:
    schema_file = tmp_path / "schema.yaml"
    schema_file.write_text(schema_yaml, encoding="utf-8")
    return generate_models(schema_file)


def test_undeclared_terms_stay_required(tmp_path):
    """Regression: classes without label/description slots keep both mandatory."""
    models = _generate(tmp_path, _SCHEMA)
    create_cls = models["PlainCreate"]
    with pytest.raises(ValidationError):
        create_cls(note="x")
    obj = create_cls(label="L", description="D")
    assert obj.label == "L"
    assert obj.description == "D"


def test_declared_optional_description(tmp_path):
    models = _generate(tmp_path, _SCHEMA)
    create_cls = models["OptionalDescriptionCreate"]
    obj = create_cls(label="L")
    assert obj.description is None

    finfo = create_cls.model_fields["description"]
    assert finfo.is_required() is False
    assert finfo.json_schema_extra == {WIKIBASE_ID: "schema:description"}
    assert finfo.description == "May be absent on existing items"

    # label was not declared and stays required
    with pytest.raises(ValidationError):
        create_cls(description="D")


def test_declared_optional_label_and_description(tmp_path):
    models = _generate(tmp_path, _SCHEMA)
    create_cls = models["OptionalBothCreate"]
    obj = create_cls()
    assert obj.label is None
    assert obj.description is None
    assert create_cls.model_fields["label"].json_schema_extra == {WIKIBASE_ID: "rdfs:label"}


def test_slot_usage_requiredness_override(tmp_path):
    """slot_usage can flip a globally optional term slot back to required."""
    models = _generate(tmp_path, _SCHEMA)
    create_cls = models["RequiredAgainCreate"]
    with pytest.raises(ValidationError):
        create_cls(label="L")
    obj = create_cls(label="L", description="D")
    assert obj.description == "D"


def test_update_model_stays_partial(tmp_path):
    models = _generate(tmp_path, _SCHEMA)
    for cls_name in ("Plain", "OptionalDescription", "RequiredAgain"):
        update_cls = models[f"{cls_name}Update"]
        obj = update_cls()
        assert obj.label is None
        assert obj.description is None


def test_wikibase_id_annotation_rejected(tmp_path):
    schema = (
        _BOILERPLATE
        + """
slots:
  description:
    range: string
    annotations:
      wikibase_id: "https://example.org/prop/direct/P2"

classes:
  Bad:
    annotations:
      python_base: entity_item
    slots:
      - description
"""
    )
    with pytest.raises(ValueError, match="wikibase_id"):
        _generate(tmp_path, schema)


def test_multivalued_rejected(tmp_path):
    schema = (
        _BOILERPLATE
        + """
slots:
  label:
    range: string
    multivalued: true

classes:
  Bad:
    annotations:
      python_base: entity_item
    slots:
      - label
"""
    )
    with pytest.raises(ValueError, match="multivalued"):
        _generate(tmp_path, schema)


def test_read_item_without_description(tmp_path):
    """An item lacking a description validates against a model with an optional description."""
    models = _generate(tmp_path, _SCHEMA)
    item = WikibaseIntegrator().item.new()
    item.labels.set("en", "Test")

    model = get_model_from_item(item, models["OptionalDescriptionBase"])
    assert model.label == "Test"
    assert model.description is None

    with pytest.raises(ValidationError):
        get_model_from_item(item, models["PlainBase"])

    # The read model is lenient: even undeclared (required) terms may be absent.
    lenient = get_model_from_item(item, models["Plain"])
    assert lenient.label == "Test"
    assert lenient.description is None


def test_entity_schema_metadata(tmp_path):
    """Form metadata reflects model requiredness; label/description stay first."""
    models = _generate(tmp_path, _SCHEMA)

    schema = _build_entity_schema("OptionalDescription", models["OptionalDescriptionCreate"], models, [])
    fields = schema["fields"]
    assert [f["name"] for f in fields[:2]] == ["label", "description"]
    by_name = {f["name"]: f for f in fields}
    assert by_name["label"]["required"] is True
    assert by_name["description"]["required"] is False
    assert by_name["description"]["description"] == "May be absent on existing items"

    plain = _build_entity_schema("Plain", models["PlainCreate"], models, [])
    plain_by_name = {f["name"]: f for f in plain["fields"]}
    assert plain_by_name["label"]["required"] is True
    assert plain_by_name["description"]["required"] is True

    # The metadata's required flags come from the Create model; the read model itself is lenient.
    assert models["Plain"].model_fields["label"].is_required() is False
    assert models["Plain"].model_fields["description"].is_required() is False
