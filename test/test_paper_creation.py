import textwrap
import unittest
from datetime import datetime
from string import Template

import requests
from pydantic import AnyHttpUrl
from wikibaseintegrator import datatypes
from wikibaseintegrator.entities import ItemEntity

from ceur_graph.ceur_dev import CeurDev
from ceur_graph.datamodel.auth import WikibaseBotAuth
from ceur_graph.datamodel.paper import Paper
from settings import Settings


class TestPaperCreation(unittest.TestCase):
    def setUp(self):
        settings = Settings()
        auth = WikibaseBotAuth(
            user=settings.WIKIBASE_BOT_USERNAME, password=settings.WIKIBASE_BOT_PASSWORD
        )
        self.ceur_dev = CeurDev(auth)

    def get_volume_paper_records(self, volume_number: int) -> list[dict]:
        """
        Get paper records for a given volume number.
        :param volume_number: volume number
        :return: list of paper records
        """
        endpoint_url = Template(
            "https://ceurspt.wikidata.dbis.rwth-aachen.de/volume/$volume_number/paper"
        )
        url = endpoint_url.substitute(volume_number=volume_number)
        response = requests.get(url)
        return response.json()

    def prepare_paper(self, record: dict, published_in: str) -> Paper | None:
        """
        Prepare the paper object by converting the given paper record into a paper object.
        :param record: paper record
        :param published_in: Qid of the proceedings the paper was published in
        :return: Paper
        """
        volume_number = record.get("spt.volume", {}).get("number")
        title = record.get("spt.title")

        acronym = record.get("spt.volume", {}).get("acronym")
        if acronym is not None:
            description = f"{acronym} paper"
        else:
            date = datetime.fromisoformat(record.get("spt.volume", {}).get("date"))
            description = f"ceur-ws paper {date.year}"
        pdf_name = record.get("cvb.pdf_name")
        if pdf_name is None or volume_number is None:
            return None
        else:
            pdf_name = pdf_name.removeprefix(f"http://ceur-ws.org/Vol-{volume_number}/")
            pdf_name = pdf_name.removeprefix(
                f"https://ceur-ws.org/Vol-{volume_number}/"
            )
            pdf_url = f"https://ceur-ws.org/Vol-{volume_number}/" + pdf_name
            if title is None:
                label = f"unknown title ({pdf_name})"
            else:
                title = " ".join(title.split())
                label = textwrap.shorten(title, width=247, placeholder="...")

            paper = Paper(
                title=title,
                label=label,
                description=description,
                full_work_available_at_url=AnyHttpUrl(pdf_url),
                published_in=published_in,
            )
            return paper

    def create_paper_item(self, paper: Paper) -> ItemEntity:
        """
        Creates a ItemEntity from the given paper object.
        :param paper: paper object
        :return: ItemEntity
        """
        item: ItemEntity = self.ceur_dev.wbi.item.new()
        item.labels.set("en", paper.label)
        item.descriptions.set("en", paper.description)
        if paper.title:
            title_pid = self.ceur_dev.get_entity_id(
                Paper.model_fields.get("title").json_schema_extra.get("ceur-dev_id")
            )
            title = datatypes.MonolingualText(
                language="en", text=paper.title, prop_nr=title_pid
            )
            item.claims.add(title)
        full_work_available_at_url_pid = self.ceur_dev.get_entity_id(
            Paper.model_fields.get("full_work_available_at_url").json_schema_extra.get(
                "ceur-dev_id"
            )
        )
        item.claims.add(
            datatypes.URL(
                paper.full_work_available_at_url.unicode_string(),
                prop_nr=full_work_available_at_url_pid,
            )
        )
        proceedings_qid = self.ceur_dev.get_entity_id(paper.published_in)
        published_in_pid = self.ceur_dev.get_entity_id(
            Paper.model_fields.get("published_in").json_schema_extra.get("ceur-dev_id")
        )
        item.claims.add(datatypes.Item(value=proceedings_qid, prop_nr=published_in_pid))
        return item

    def create_volume_papers(self, volume_number: int):
        """
        For the given volume number, create the paper entries in ceur-dev
        :param volume_number: volume number
        :return: None
        """
        paper_records = self.get_volume_paper_records(volume_number)
        if isinstance(paper_records, dict):
            print(f"Volume {volume_number} does not exist")
            return
        published_in = CeurDev().get_proceedings_by_volume_number(volume_number)
        for i, paper_record in enumerate(paper_records):
            print(f"{i}/{len(paper_records)} Crating paper for volume {volume_number}")
            paper = self.prepare_paper(paper_record, published_in)
            if paper is None:
                print(f"Skipping {i} paper of volume {volume_number}")
                continue
            if self.paper_exists(paper):
                print(
                    f"Paper item already exists → Skipping {i} paper for volume {volume_number}"
                )
                continue
            paper_item = self.create_paper_item(paper)
            self.ceur_dev.write_item(paper_item)

    def paper_exists(self, paper: Paper) -> bool:
        """
        Check if the given paper exists in the ceur-dev database.
        The paper pdf id is used for the existence check
        :param paper: Paper to check
        :return: True if the paper exists in the ceur-dev database. Otherwise False
        """
        query_template = Template("""
        PREFIX wdt: <https://ceur-dev.wikibase.cloud/prop/direct/>
        PREFIX wd: <https://ceur-dev.wikibase.cloud/entity/>
        ASK{?paper wdt:P12 <$pdf_url>. }
        """)
        query = query_template.substitute(
            pdf_url=paper.full_work_available_at_url.unicode_string()
        )
        item_exists = self.ceur_dev.execute_ask_query(
            query, self.ceur_dev.sparql_endpoint
        )
        return item_exists

    @unittest.skip("For manual use")
    def test_creation_of_volume_range(self):
        for volume_number in range(3497, 3500):
            print(volume_number)
            self.create_volume_papers(volume_number)

    @unittest.skip("For manual use")
    def test_creation_of_specific_volume(self):
        self.create_volume_papers(3500)

    @unittest.skip("For manual use")
    def test_login_credentials(self):
        """
        test login with the credentials
        """
        self.ceur_dev.get_wbi_login()
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
