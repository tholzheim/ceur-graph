import unittest

from wikibaseintegrator.wbi_enums import WikibaseSnakType

from wbforms.codegen import Subject, SubjectCreate
from wbforms.datamodel.item import WIKIBASE_ID


class TestSubject(unittest.TestCase):
    def test_subject_fieldinfo(self):
        subject_field = Subject.get_statement_subject(WIKIBASE_ID)
        self.assertEqual("subject_id", subject_field)

    def test_loading_from_record(self):
        subject_record = {"subject_id": "somevalue", "object_named_as": "Wikidata"}
        subject = SubjectCreate.model_validate(subject_record)
        self.assertEqual(WikibaseSnakType.UNKNOWN_VALUE.value, subject.subject_id)


if __name__ == "__main__":
    unittest.main()
