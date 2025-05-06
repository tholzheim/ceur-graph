import unittest

from fastapi.testclient import TestClient

from ceur_graph.main import app

client = TestClient(app)


def test_get_volume_paper_ids():
    volume_number = 3450
    expected_qid = "https://ceur-dev.wikibase.cloud/entity/Q19618"
    expected_documents = 6
    volume_documents = client.get(f"/ceur-ws/Vol-{volume_number}/papers").json()
    assert expected_qid in volume_documents
    assert expected_documents == len(volume_documents)


def test_get_volume_id():
    volume_number = 3450
    expected_qid = "https://ceur-dev.wikibase.cloud/entity/Q8940"
    expected_documents = 6
    volume_qid = client.get(f"/ceur-ws/Vol-{volume_number}").json()
    assert expected_qid == volume_qid

if __name__ == "__main__":
    unittest.main()
