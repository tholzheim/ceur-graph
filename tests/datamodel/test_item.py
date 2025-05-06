import unittest

from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.subject import SubjectBase


class TestExtractedStatement(unittest.TestCase):
    def test_object_named_as_required(self):
        """
        tests if object_named_as is required if the statement object is unknown
        """
        record = {"subject_id": WikibaseSnakType.UNKNOWN_VALUE.value}
        self.assertRaises(ValueError, SubjectBase.model_validate, record)

        record["object_named_as"] = "tests"
        subject = SubjectBase.model_validate(record)
        self.assertIsInstance(subject, SubjectBase)

    def test_equivalence(self):
        params = [
            (
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                True,
            ),
            (
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                SubjectBase(subject_id="Q1"),
                True,
            ),
            (
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                SubjectBase(subject_id="Q1", object_named_as="diff"),
                False,
            ),
            (
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                SubjectBase(
                    subject_id=WikibaseSnakType.UNKNOWN_VALUE.value,
                    object_named_as="tests",
                ),
                True,
            ),
            (
                SubjectBase(
                    subject_id=WikibaseSnakType.UNKNOWN_VALUE.value,
                    object_named_as="tests",
                ),
                SubjectBase(
                    subject_id=WikibaseSnakType.UNKNOWN_VALUE.value,
                    object_named_as="tests",
                ),
                True,
            ),
            (
                SubjectBase(subject_id="Q1", object_named_as="tests"),
                SubjectBase(subject_id="Q2", object_named_as="diff"),
                False,
            ),
            (
                SubjectBase(
                    subject_id=WikibaseSnakType.UNKNOWN_VALUE.value,
                    object_named_as="string42",
                ),
                SubjectBase(
                    object_named_as="string42",
                ),
                True,
            ),
        ]
        for subject1, subject2, expected_equal in params:
            with self.subTest(subject1=subject1, subject2=subject2):
                self.assertEqual(expected_equal, subject1 == subject2)


if __name__ == "__main__":
    unittest.main()
