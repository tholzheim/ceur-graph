import unittest

from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.item import CEUR_DEV_ID
from ceur_graph.datamodel.subject import Subject, SubjectCreate


class TestSubject(unittest.TestCase):
    def test_subject_fieldinfo(self):
        subject_field = Subject.get_statement_subject(CEUR_DEV_ID)
        self.assertEqual("subject_id", subject_field)

    def test_loading_from_record(self):
        subject_record = {"subject_id": "somevalue", "object_named_as": "Wikidata"}
        subject = SubjectCreate.model_validate(subject_record)
        self.assertEqual(WikibaseSnakType.UNKNOWN_VALUE.value, subject.subject_id)


if __name__ == "__main__":
    unittest.main()
