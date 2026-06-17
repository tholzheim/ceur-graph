"""In-memory tests for qualifier handling in update_qualified_statement_from_model.

These exercise the wbgenerator code paths against in-memory Claim/Item objects
only — no Wikibase network calls are made.
"""

import unittest

from wikibaseintegrator.entities import ItemEntity

from ceur_graph.codegen import get_models
from ceur_graph.wbgenerator import (
    create_qualified_statement_from_model,
    get_model_from_qualified_statement,
    update_qualified_statement_from_model,
)


class TestQualifierUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m = get_models()
        cls.Create = m["ScholarSignatureCreate"]
        cls.Update = m["ScholarSignatureUpdate"]
        cls.Read = m["ScholarSignature"]

    def _item_with_signature(self, **create_kwargs):
        sig = self.Create(**create_kwargs)
        claim = create_qualified_statement_from_model(sig)
        claim.id = "Q1$dummyguid"
        item = ItemEntity()
        item.id = "Q1"
        item.claims.add(claim)
        return item, claim

    def _apply_update(self, item, claim, body):
        upd = self.Update.model_validate(body)
        update_qualified_statement_from_model(item, claim.id, upd)
        return get_model_from_qualified_statement(claim, self.Read)

    def test_clear_multivalue_qualifier(self):
        """Clearing a multi-value qualifier removes every value (mutate-during-iteration regression)."""
        item, claim = self._item_with_signature(scholar_id="Q42", affiliation=["Q1", "Q2", "Q3"])
        back = self._apply_update(item, claim, {"scholar_id": "Q42", "affiliation": []})
        self.assertEqual(back.affiliation, [])

    def test_clear_even_count_multivalue_qualifier(self):
        item, claim = self._item_with_signature(scholar_id="Q42", affiliation=["Q1", "Q2", "Q3", "Q4"])
        back = self._apply_update(item, claim, {"scholar_id": "Q42", "affiliation": []})
        self.assertEqual(back.affiliation, [])

    def test_replace_multivalue_qualifier(self):
        """Replacing a multi-value qualifier must not leave stale values behind."""
        item, claim = self._item_with_signature(scholar_id="Q42", affiliation=["Q1", "Q2", "Q3"])
        back = self._apply_update(item, claim, {"scholar_id": "Q42", "affiliation": ["Q9"]})
        self.assertEqual(back.affiliation, ["Q9"])

    def test_clear_single_value_qualifier(self):
        """Sanity: single-value qualifier clearing still works."""
        item, claim = self._item_with_signature(scholar_id="Q42", series_ordinal=1)
        back = self._apply_update(item, claim, {"scholar_id": "Q42", "series_ordinal": ""})
        self.assertIsNone(back.series_ordinal)


if __name__ == "__main__":
    unittest.main()
