import json
import os

from gadi import models
from gadi.gesetze_im_internet import download, parsing

example_json_dir = os.path.join(os.path.dirname(__file__), "..", "example_json")
xml_fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "gii_xml")


def load_example_json(slug):
    with open(os.path.join(example_json_dir, slug + ".json")) as f:
        return json.load(f)


def load_law_from_fixture(slug):
    location = download.LocalPathLocation(xml_fixtures_dir)
    xml_filename = location.xml_file_for(slug)
    law_dict = parsing.parse_law(xml_filename)
    law_dict["attachments"] = location.attachments(slug)
    law = models.Law.from_dict(law_dict, slug)
    return law
