"""In-memory tests for qualifier handling in update_qualified_statement_from_model.

These exercise the wbgenerator code paths against in-memory Claim/Item objects
only — no Wikibase network calls are made.
"""

import unittest

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.entities import ItemEntity

from wbforms.codegen import get_models
from wbforms.wbgenerator import (
    StatementNotFoundError,
    create_item_from_model,
    create_qualified_statement_from_model,
    get_model_from_item,
    get_model_from_qualified_statement,
    update_item_from_model,
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

    def test_unknown_statement_id_raises_diagnostic_error(self):
        """An unknown statement_id raises StatementNotFoundError listing the available ids."""
        item, claim = self._item_with_signature(scholar_id="Q42", affiliation=["Q1"])
        upd = self.Update.model_validate({"scholar_id": "Q42", "affiliation": ["Q9"]})
        with self.assertRaises(StatementNotFoundError) as ctx:
            update_qualified_statement_from_model(item, "Q1$does-not-exist", upd)
        err = ctx.exception
        self.assertEqual(err.statement_id, "Q1$does-not-exist")
        self.assertIn(claim.id, err.available_ids)
        self.assertIn(claim.id, str(err))


class TestItemUpdatePreservesStatements(unittest.TestCase):
    """A direct-property item update must leave untouched qualified statements (and their
    qualifiers) intact.

    This guards the reported "editing a plain property wipes qualifiers" scenario:
    ``update_item_from_model`` only walks ``model.model_fields_set``, so a partial update that
    carries a single direct field never enters the statement-reference wipe-and-rebuild branch.
    """

    @classmethod
    def setUpClass(cls):
        m = get_models()
        cls.PaperCreate = m["PaperCreate"]
        cls.PaperUpdate = m["PaperUpdate"]
        cls.Paper = m["Paper"]

    def _paper_item(self):
        """Build a persisted-looking Paper item: one author signature with qualifiers, plus
        direct properties. Claim ids are assigned to mimic an item fetched from Wikibase."""
        paper = self.PaperCreate.model_validate(
            {
                "label": "Original title",
                "description": "test paper",
                "title": "Original title",
                "published_in": "Q100",
                "full_work_available_at_url": "https://example.org/paper.pdf",
                "pages": 5,
                "authors": [
                    {
                        "statement_id": "Q1",
                        "scholar_id": "Q42",
                        "affiliation": ["Q1", "Q2"],
                        "series_ordinal": 1,
                    }
                ],
            }
        )
        item = create_item_from_model(paper, WikibaseIntegrator())
        item.id = "Q1"
        # Assign stable claim ids as a real read-modify-write would have.
        idx = 0
        for claim_list in item.claims.claims.values():
            for claim in claim_list:
                claim.id = f"Q1$claim-{idx}"
                idx += 1
        return item

    def test_direct_property_update_preserves_qualified_statement(self):
        item = self._paper_item()
        before = get_model_from_item(item, self.Paper)
        author_ids_before = [a.statement_id for a in before.authors]
        self.assertEqual(len(author_ids_before), 1)

        # Partial update carrying ONLY a direct property.
        update_item_from_model(model=self.PaperUpdate.model_validate({"pages": 10}), item=item)

        after = get_model_from_item(item, self.Paper)
        # Direct property changed...
        self.assertEqual(after.pages, 10)
        # ...the author statement is the same one (not wiped and re-added)...
        self.assertEqual([a.statement_id for a in after.authors], author_ids_before)
        # ...and its qualifiers survive untouched.
        self.assertEqual(after.authors[0].affiliation, ["Q1", "Q2"])
        self.assertEqual(after.authors[0].series_ordinal, 1)

    def test_partial_update_excludes_untouched_statement_fields(self):
        """A partial Update model only reports the fields actually sent, so the
        statement-reference branch of update_item_from_model is never entered for them."""
        upd = self.PaperUpdate.model_validate({"pages": 10})
        self.assertIn("pages", upd.model_fields_set)
        self.assertNotIn("authors", upd.model_fields_set)


if __name__ == "__main__":
    unittest.main()
