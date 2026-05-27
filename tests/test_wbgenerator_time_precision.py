"""Tests for Wikibase time precision inference in wbgenerator."""

import unittest

from wikibaseintegrator import datatypes

from ceur_graph.wbgenerator import _infer_time_precision, get_claim


class TestInferTimePrecision(unittest.TestCase):
    def test_year_precision_when_month_and_day_zero(self):
        self.assertEqual(_infer_time_precision("+2020-00-00T00:00:00Z"), 9)

    def test_month_precision_when_only_day_zero(self):
        self.assertEqual(_infer_time_precision("+2020-05-00T00:00:00Z"), 10)

    def test_day_precision_when_all_date_parts_set(self):
        self.assertEqual(_infer_time_precision("+2026-05-20T00:00:00Z"), 11)

    def test_sub_day_fields_are_clamped_to_day(self):
        # WikibaseIntegrator's precision enum stops at DAY (11), so sub-day
        # components (hour/min/sec) collapse to day precision rather than
        # error out at write time.
        self.assertEqual(_infer_time_precision("+2026-05-20T13:45:30Z"), 11)

    def test_negative_year_handled(self):
        self.assertEqual(_infer_time_precision("-0044-03-15T00:00:00Z"), 11)

    def test_fallback_for_invalid_format(self):
        self.assertEqual(_infer_time_precision("not-a-date"), 11)
        self.assertEqual(_infer_time_precision(""), 11)


class TestGetClaimTimePrecision(unittest.TestCase):
    """Verify get_claim wires the inferred precision into the Wikibase Time datavalue."""

    def _precision(self, time_str: str) -> int:
        claim = get_claim(prop_id="P24", datatype=datatypes.Time.DTYPE, value=time_str)
        return claim.mainsnak.datavalue["value"]["precision"]

    def test_year_precision_round_trips_through_get_claim(self):
        self.assertEqual(self._precision("+2020-00-00T00:00:00Z"), 9)

    def test_month_precision_round_trips_through_get_claim(self):
        self.assertEqual(self._precision("+2020-05-00T00:00:00Z"), 10)

    def test_day_precision_round_trips_through_get_claim(self):
        self.assertEqual(self._precision("+2026-05-20T00:00:00Z"), 11)


if __name__ == "__main__":
    unittest.main()
