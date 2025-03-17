from unittest import TestCase

from ceur_graph.ceur_dev import CeurDev


class TestCeurDev(TestCase):
    def test_get_proceedings_by_volume_number_query(self):
        volume_number = 3658
        actual_query = CeurDev.get_proceedings_by_volume_number_query(volume_number)
        self.assertIn(str(volume_number), actual_query)

    def test_get_proceedings_by_volume_number(self):
        volume_number = 3658
        expected_qid = "https://ceur-dev.wikibase.cloud/entity/Q9402"
        actual_qid = CeurDev().get_proceedings_by_volume_number(volume_number)
        self.assertEqual(expected_qid, actual_qid)
