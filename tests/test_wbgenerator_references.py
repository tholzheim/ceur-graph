"""In-memory round-trip tests for Wikibase statement-level references."""

import unittest

from wbforms.codegen import get_models
from wbforms.wbgenerator import (
    add_references_to_statement,
    create_qualified_statement_from_model,
    get_model_from_qualified_statement,
    populate_references_from_claim,
)


class TestReferencesRoundTrip(unittest.TestCase):
    """
    These tests exercise the wbgenerator code paths against in-memory Claim
    objects only — no Wikibase network calls are made.
    """

    @classmethod
    def setUpClass(cls):
        m = get_models()
        cls.ScholarSignatureCreate = m["ScholarSignatureCreate"]
        cls.ScholarSignatureUpdate = m["ScholarSignatureUpdate"]
        cls.ScholarSignature = m["ScholarSignature"]
        cls.WikibaseReference = m["WikibaseReference"]
        cls.Reference = m["Reference"]
        cls.ReferenceCreate = m["ReferenceCreate"]

    def _make_signature_with_two_sources(self):
        return self.ScholarSignatureCreate(
            scholar_id="Q42",
            series_ordinal=1,
            sources=[
                self.WikibaseReference(
                    stated_in="Q100",
                    reference_url="https://example.org/page",
                    retrieved="+2026-05-20T00:00:00Z",
                ),
                self.WikibaseReference(stated_in="Q200"),
            ],
        )

    def test_create_attaches_reference_blocks(self):
        sig = self._make_signature_with_two_sources()
        claim = create_qualified_statement_from_model(sig)

        self.assertEqual(len(claim.references), 2)
        # First block carries all three snaks
        block0_props = sorted(claim.references.references[0].snaks.snaks.keys())
        self.assertEqual(block0_props, ["P24", "P34", "P66"])  # retrieved, stated_in, reference_url
        # Second block has only stated_in
        block1_props = sorted(claim.references.references[1].snaks.snaks.keys())
        self.assertEqual(block1_props, ["P34"])

    def test_read_back_round_trips(self):
        sig = self._make_signature_with_two_sources()
        claim = create_qualified_statement_from_model(sig)
        claim.id = "Q42$dummy"

        back = get_model_from_qualified_statement(claim, self.ScholarSignature)
        self.assertEqual(len(back.sources), 2)
        self.assertEqual(back.sources[0].stated_in, "Q100")
        self.assertEqual(str(back.sources[0].reference_url), "https://example.org/page")
        self.assertEqual(back.sources[0].retrieved, "+2026-05-20T00:00:00Z")
        self.assertEqual(back.sources[1].stated_in, "Q200")
        self.assertIsNone(back.sources[1].reference_url)
        self.assertIsNone(back.sources[1].retrieved)

    def test_update_replaces_reference_blocks(self):
        sig = self._make_signature_with_two_sources()
        claim = create_qualified_statement_from_model(sig)
        claim.id = "Q42$dummy"
        self.assertEqual(len(claim.references), 2)

        # Replace with one new block
        new_sig = self.ScholarSignatureUpdate(
            sources=[self.WikibaseReference(stated_in="Q300", reference_url="https://updated.example.org")],
        )
        claim.references.clear()
        add_references_to_statement(claim, new_sig)
        self.assertEqual(len(claim.references), 1)

        back = get_model_from_qualified_statement(claim, self.ScholarSignature)
        self.assertEqual(len(back.sources), 1)
        self.assertEqual(back.sources[0].stated_in, "Q300")

    def test_empty_source_block_is_skipped(self):
        """A WikibaseReference with all-None fields produces no reference block."""
        sig = self.ScholarSignatureCreate(
            scholar_id="Q1",
            sources=[self.WikibaseReference()],
        )
        claim = create_qualified_statement_from_model(sig)
        self.assertEqual(len(claim.references), 0)

    def test_statement_without_sources_round_trips(self):
        sig = self.ScholarSignatureCreate(scholar_id="Q1", series_ordinal=1)
        claim = create_qualified_statement_from_model(sig)
        claim.id = "Q1$x"
        self.assertEqual(len(claim.references), 0)

        back = get_model_from_qualified_statement(claim, self.ScholarSignature)
        self.assertEqual(back.sources, [])

    def test_non_opted_in_statement_class_is_unaffected(self):
        """The bibliographic Reference class has no `sources` field and is untouched."""
        ref = self.ReferenceCreate(reference_id="Q5", doi="10.1/abc", title="Test paper")
        claim = create_qualified_statement_from_model(ref)
        claim.id = "Q5$y"

        # Reading back must not crash even though the class has no sources field
        back = get_model_from_qualified_statement(claim, self.Reference)
        self.assertEqual(back.reference_id, "Q5")
        self.assertFalse(hasattr(back, "sources"))

        # populate_references_from_claim returns None when sources isn't on the class
        self.assertIsNone(populate_references_from_claim(claim, self.Reference))


if __name__ == "__main__":
    unittest.main()
