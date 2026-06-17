import unittest

from fastapi import HTTPException, status
from wikibaseintegrator.entities import ItemEntity

from ceur_graph.api.utils import get_model_label, handle_statement_update
from ceur_graph.codegen import ScholarSignature, SubjectBase, get_models
from ceur_graph.wbgenerator import create_qualified_statement_from_model


class _FakeWikibase:
    """Returns a fixed in-memory item; write must never be reached for the 404 path."""

    def __init__(self, item: ItemEntity):
        self._item = item

    def get_item(self, item_id: str) -> ItemEntity:
        return self._item

    def write_item(self, *args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("write_item should not be called when the statement is missing")


class TestUtils(unittest.TestCase):
    """
    tests utility functions
    """

    def test_get_model_label(self):
        self.assertEqual("scholar signature", get_model_label(ScholarSignature))

        self.assertEqual("subject", get_model_label(SubjectBase))

    def test_update_missing_statement_returns_404(self):
        """A statement_id absent from the item yields a 404 (not a 500)."""
        models = get_models()
        sig = models["ScholarSignatureCreate"](scholar_id="Q42", affiliation=["Q1"])
        claim = create_qualified_statement_from_model(sig)
        claim.id = "Q1$realguid"
        item = ItemEntity()
        item.id = "Q1"
        item.claims.add(claim)

        upd = models["ScholarSignatureUpdate"].model_validate({"scholar_id": "Q42", "affiliation": ["Q9"]})
        with self.assertRaises(HTTPException) as ctx:
            handle_statement_update(
                wikibase=_FakeWikibase(item),
                item_id="Q1",
                statement_id="Q1$missing",
                model_obj=upd,
                target_model=models["ScholarSignature"],
            )
        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Q1$realguid", ctx.exception.detail)
