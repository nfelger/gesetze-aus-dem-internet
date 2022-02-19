import base64
from email.utils import parsedate_to_datetime
import glob
from io import BytesIO
import mimetypes
import os
import shutil
from urllib.parse import urlparse
import zipfile

from lxml import etree
import requests

TOC_URL = "http://www.gesetze-im-internet.de/gii-toc.xml"


def fetch_toc():
    response = requests.get(TOC_URL)
    response.raise_for_status()

    toc = {}

    doc = etree.fromstring(response.content)
    for item in doc.xpath("/items/item"):
        url = item.find("link").text
        slug = url.split("/")[-2]
        toc[slug] = url

    return toc


def _parse_last_modified_date_str(response):
    last_modified_header = response.headers["Last-Modified"]
    return parsedate_to_datetime(last_modified_header).strftime("%Y%m%d")


def has_update(download_url, timestamp_string):
    response = requests.head(download_url)
    response.raise_for_status()

    return _parse_last_modified_date_str(response) > timestamp_string


def location_from_string(location_string):
    return LocalPathLocation(location_string)


class LocalPathLocation:
    def __init__(self, location_string):
        self.data_dir = location_string

    def remove_law(self, slug):
        shutil.rmtree(os.path.join(self.data_dir, slug), ignore_errors=True)

    def create_or_replace_law(self, slug, download_url):
        self.remove_law(slug)

        dir_path = os.path.join(self.data_dir, slug)
        os.makedirs(dir_path, exist_ok=True)

        response = requests.get(download_url)
        response.raise_for_status()

        zip_archive = zipfile.ZipFile(BytesIO(response.content))
        zip_archive.extractall(dir_path)

        timestamp = _parse_last_modified_date_str(response)
        with open(dir_path + "/.timestamp", "w") as f:
            f.write(timestamp)

    def list_slugs_with_timestamps(self):
        result = {}

        for path in glob.glob(f"{self.data_dir}/*/"):
            slug = path.split("/")[-2]
            try:
                with open(path + ".timestamp") as f:
                    result[slug] = f.read()
            except FileNotFoundError:
                print(f"Warning: No .timestamp in {path}")
                result[slug] = "00000000"

        return result

    def xml_file_for(self, slug):
        law_dir = os.path.join(self.data_dir, slug)
        xml_files = glob.glob(f"{law_dir}/*.xml")
        assert len(xml_files) == 1, f"Expected 1 XML file in {law_dir}, got {len(xml_files)}"

        return xml_files[0]

    def attachments(self, slug):
        law_dir = os.path.join(self.data_dir, slug)
        all_files = glob.glob(f"{law_dir}/*")
        attachments = {}
        for path in all_files:
            if path.endswith(".xml"):
                continue

            mimetype, _ = mimetypes.guess_type(path, strict=False)
            with open(path, "rb") as file:
                data = file.read()
            data_base64_bytes = base64.b64encode(data).decode("ascii")
            data_uri = f"data:{mimetype};base64,{data_base64_bytes}"

            attachments[os.path.basename(path)] = data_uri
        return attachments
