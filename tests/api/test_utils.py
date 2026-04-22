import unittest

from ceur_graph.api.utils import get_model_label
from ceur_graph.codegen import ScholarSignature, SubjectBase


class TestUtils(unittest.TestCase):
    """
    tests utility functions
    """

    def test_get_model_label(self):
        self.assertEqual("scholar signature", get_model_label(ScholarSignature))

        self.assertEqual("subject", get_model_label(SubjectBase))
