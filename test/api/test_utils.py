import unittest

from ceur_graph.api.utils import get_model_label
from ceur_graph.datamodel.scholarsignature import ScholarSignature
from ceur_graph.datamodel.subject import SubjectBase


class TestUtils(unittest.TestCase):
    """
    test utility functions
    """

    def test_get_model_label(self):
        self.assertEqual("scholar signature", get_model_label(ScholarSignature))

        self.assertEqual("subject", get_model_label(SubjectBase))
