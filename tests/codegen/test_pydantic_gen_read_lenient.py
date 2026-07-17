"""Tests for lenient read models: partial items load even when required fields are missing."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from wikibaseintegrator import WikibaseIntegrator

from wbforms.codegen.pydantic_gen import generate_models
from wbforms.datamodel.item import WIKIBASE_ID
from wbforms.wbgenerator import (
    create_qualified_statement_from_model,
    get_model_from_item,
    get_model_from_qualified_statement,
)

_SCHEMA = """
id: https://example.org/schema/test-read-lenient
name: test_read_lenient
description: Test schema for lenient read models

prefixes:
  linkml: https://w3id.org/linkml/

default_range: string

imports:
  - linkml:types

slots:
  note:
    range: string
    annotations:
      wikibase_id: "https://example.org/prop/direct/P1"
      wikibase_type: string
  ident:
    range: string
    required: true
    pattern: "Q\\\\d+"
    annotations:
      wikibase_id: "https://example.org/prop/direct/P2"
      wikibase_type: external-id
  scholar_id:
    range: item_statement_subject
    annotations:
      wikibase_id: "https://example.org/prop/statement/P93"
      wikibase_type: item
  ordinal:
    range: integer
    required: true
    annotations:
      wikibase_id: "https://example.org/prop/qualifier/P18"
      wikibase_type: string

classes:
  Doc:
    annotations:
      python_base: entity_item
    slots:
      - note
      - ident

  Sig:
    annotations:
      python_base: extracted_statement
    slots:
      - scholar_id
      - ordinal
"""


@pytest.fixture
def models(tmp_path: Path) -> dict[str, type]:
    schema_file = tmp_path / "schema.yaml"
    schema_file.write_text(_SCHEMA, encoding="utf-8")
    return generate_models(schema_file)


def test_read_model_is_lenient_create_stays_strict(models):
    """The read model constructs without required fields; the Create model rejects that."""
    doc = models["Doc"]()
    assert doc.label is None
    assert doc.ident is None
    assert doc.note is None

    assert models["Doc"].model_fields["ident"].is_required() is False
    assert models["Doc"].model_fields["label"].is_required() is False
    assert models["DocCreate"].model_fields["ident"].is_required() is True
    with pytest.raises(ValidationError):
        models["DocCreate"](label="L", description="D")


def test_loosened_field_keeps_metadata_and_pattern(models):
    """make_field_optional preserves json_schema_extra and pattern constraints."""
    finfo = models["Doc"].model_fields["ident"]
    extra = finfo.json_schema_extra
    assert extra[WIKIBASE_ID] == "https://example.org/prop/direct/P2"

    with pytest.raises(ValidationError):
        models["Doc"](ident="not-a-qid")
    assert models["Doc"](ident="Q5").ident == "Q5"


def test_get_model_from_item_with_missing_required_fields(models):
    """An item holding only a label loads into the read model with None gaps."""
    item = WikibaseIntegrator().item.new()
    item.labels.set("en", "Partial")

    model = get_model_from_item(item, models["Doc"])
    assert model.label == "Partial"
    assert model.description is None
    assert model.ident is None


def test_read_model_roundtrip(models):
    """model_dump → model_validate round-trip succeeds (FastAPI response re-validation)."""
    model = models["Doc"].model_validate({"label": "L"})
    revalidated = models["Doc"].model_validate(model.model_dump())
    assert revalidated.label == "L"
    assert revalidated.ident is None


def test_statement_read_is_lenient(models):
    """A claim missing a required qualifier still maps to the read statement model."""
    partial = models["SigUpdate"].model_validate({"scholar_id": "Q42"})
    claim = create_qualified_statement_from_model(partial)
    claim.id = "Q1$guid"

    stmt = get_model_from_qualified_statement(claim, models["Sig"])
    assert stmt.scholar_id == "Q42"
    assert stmt.ordinal is None
    assert stmt.statement_id == "Q1$guid"

    with pytest.raises(ValidationError):
        models["SigCreate"](scholar_id="Q42")


def test_statement_id_stays_required_on_read(models):
    """statement_id comes from claim.id on read and is intentionally not loosened."""
    assert models["Sig"].model_fields["statement_id"].is_required() is True
