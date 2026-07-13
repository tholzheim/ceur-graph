"""In-memory round-trip tests for Wikibase references on direct (non-qualified) properties."""

import unittest

from wikibaseintegrator import WikibaseIntegrator

from wbforms.codegen import get_models
from wbforms.wbgenerator import (
    create_item_from_model,
    get_model_from_item,
    update_item_from_model,
)


class TestDirectPropertyReferencesRoundTrip(unittest.TestCase):
    """
    Exercise direct-property reference handling against in-memory ItemEntity
    objects only — no Wikibase network calls are made.
    """

    @classmethod
    def setUpClass(cls):
        m = get_models()
        cls.PaperCreate = m["PaperCreate"]
        cls.PaperUpdate = m["PaperUpdate"]
        cls.Paper = m["Paper"]
        cls.VolumeCreate = m["VolumeCreate"]
        cls.VolumeUpdate = m["VolumeUpdate"]
        cls.Volume = m["Volume"]
        cls.WikibaseReference = m["WikibaseReference"]
        cls.wbi = WikibaseIntegrator()

    def _make_paper_with_title_source(self, stated_in_qid: str = "Q100"):
        return self.PaperCreate(
            label="Test paper",
            description="A test",
            title="Hello world",
            published_in="Q1",
            full_work_available_at_url="https://example.org/p.pdf",
            title_sources=[
                self.WikibaseReference(
                    stated_in=stated_in_qid,
                    reference_url="https://example.org/source",
                ),
            ],
        )

    # --- Single-valued: Paper.title ---

    def test_create_attaches_references_to_direct_claim(self):
        paper = self._make_paper_with_title_source()
        item = create_item_from_model(paper, self.wbi)
        # P5 = title
        title_claims = item.claims.get("P5")
        self.assertEqual(len(title_claims), 1)
        self.assertEqual(len(title_claims[0].references), 1)
        block = title_claims[0].references.references[0]
        self.assertIn("P34", block.snaks.snaks)  # stated_in
        self.assertIn("P66", block.snaks.snaks)  # reference_url

    def test_read_back_direct_property_references(self):
        paper = self._make_paper_with_title_source()
        item = create_item_from_model(paper, self.wbi)
        back = get_model_from_item(item, self.PaperUpdate)
        self.assertEqual(len(back.title_sources), 1)
        self.assertEqual(back.title_sources[0].stated_in, "Q100")
        self.assertEqual(str(back.title_sources[0].reference_url), "https://example.org/source")

    def test_update_sources_only_replaces_references(self):
        paper = self._make_paper_with_title_source(stated_in_qid="Q100")
        item = create_item_from_model(paper, self.wbi)
        update_item_from_model(
            self.PaperUpdate(title_sources=[self.WikibaseReference(stated_in="Q200")]),
            item,
        )
        title_claims = item.claims.get("P5")
        self.assertEqual(len(title_claims), 1)
        self.assertEqual(len(title_claims[0].references), 1)
        block = title_claims[0].references.references[0]
        snak = block.snaks.snaks["P34"][0]
        self.assertEqual(snak.datavalue["value"]["id"], "Q200")

    def test_update_sources_only_with_empty_list_clears_references(self):
        paper = self._make_paper_with_title_source()
        item = create_item_from_model(paper, self.wbi)
        update_item_from_model(self.PaperUpdate(title_sources=[]), item)
        title_claims = item.claims.get("P5")
        self.assertEqual(len(title_claims[0].references), 0)

    def test_empty_source_block_is_skipped_for_direct(self):
        paper = self.PaperCreate(
            label="P",
            description="d",
            title="H",
            published_in="Q1",
            full_work_available_at_url="https://example.org/p.pdf",
            title_sources=[self.WikibaseReference()],
        )
        item = create_item_from_model(paper, self.wbi)
        title_claims = item.claims.get("P5")
        self.assertEqual(len(title_claims[0].references), 0)

    def test_paper_without_sources_round_trips(self):
        paper = self.PaperCreate(
            label="P",
            description="d",
            title="H",
            published_in="Q1",
            full_work_available_at_url="https://example.org/p.pdf",
        )
        item = create_item_from_model(paper, self.wbi)
        title_claims = item.claims.get("P5")
        self.assertEqual(len(title_claims[0].references), 0)
        back = get_model_from_item(item, self.PaperUpdate)
        self.assertEqual(back.title_sources, [])

    # --- Multivalued: Volume.is_proceedings_from ---

    def _make_volume_with_proceedings(self):
        return self.VolumeCreate(
            label="V",
            description="d",
            is_proceedings_from=["Q10", "Q20", "Q30"],
            is_proceedings_from_sources=[
                [self.WikibaseReference(stated_in="Q100")],
                [],
                [
                    self.WikibaseReference(stated_in="Q300"),
                    self.WikibaseReference(stated_in="Q301"),
                ],
            ],
        )

    def test_create_attaches_positional_references_multivalued(self):
        vol = self._make_volume_with_proceedings()
        item = create_item_from_model(vol, self.wbi)
        claims = item.claims.get("P16")
        self.assertEqual(len(claims), 3)
        self.assertEqual(len(claims[0].references), 1)
        self.assertEqual(len(claims[1].references), 0)
        self.assertEqual(len(claims[2].references), 2)

    def test_read_back_positional_references_multivalued(self):
        vol = self._make_volume_with_proceedings()
        item = create_item_from_model(vol, self.wbi)
        back = get_model_from_item(item, self.VolumeUpdate)
        self.assertEqual(len(back.is_proceedings_from_sources), 3)
        self.assertEqual(len(back.is_proceedings_from_sources[0]), 1)
        self.assertEqual(back.is_proceedings_from_sources[0][0].stated_in, "Q100")
        self.assertEqual(back.is_proceedings_from_sources[1], [])
        self.assertEqual(len(back.is_proceedings_from_sources[2]), 2)

    def test_update_replaces_positional_references_multivalued(self):
        vol = self._make_volume_with_proceedings()
        item = create_item_from_model(vol, self.wbi)
        # Replace values + sources entirely.
        update_item_from_model(
            self.VolumeUpdate(
                is_proceedings_from=["Q40", "Q50"],
                is_proceedings_from_sources=[
                    [],
                    [self.WikibaseReference(stated_in="Q500")],
                ],
            ),
            item,
        )
        # Filter out claims marked removed in-memory (only live claims would be persisted).
        live_claims = [c for c in item.claims.get("P16") if not c.removed]
        self.assertEqual(len(live_claims), 2)
        self.assertEqual(len(live_claims[0].references), 0)
        self.assertEqual(len(live_claims[1].references), 1)


if __name__ == "__main__":
    unittest.main()
