from email.utils import parsedate_to_datetime
import glob
from io import BytesIO
import os
import shutil
from urllib.parse import urlparse
import zipfile

import boto3
import botocore
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
    if location_string.startswith("s3://"):
        return S3Location(location_string)
    else:
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


class S3Location:
    def __init__(self, location_string):
        # Cf. https://stackoverflow.com/a/44478894/11819
        # "With boto3, the S3 urls are virtual by default, which then require internet access to be
        # resolved to region specific urls. This causes the hanging of the Lambda function until
        # timeout."
        self.s3 = boto3.client(
            "s3", "eu-central-1", config=botocore.config.Config(s3={"addressing_style": "path"})
        )

        parsed_url = urlparse(location_string)
        self.bucket = parsed_url.netloc
        self.key_prefix = parsed_url.path[1:]  # omit initial slash
        if not self.key_prefix.endswith("/"):
            self.key_prefix += "/"

    def _law_prefix(self, slug):
        return f"{self.key_prefix}{slug}/"

    def _list_keys(self, prefix):
        paginator = self.s3.get_paginator("list_objects").paginate(Bucket=self.bucket, Prefix=prefix)
        keys = []
        for page in paginator:
            keys += [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
        return keys

    def _upload_file(self, slug, name, body):
        prefix = self._law_prefix(slug)
        self.s3.put_object(Bucket=self.bucket, Key=f"{prefix}{name}", Body=body)

    def _fetch_file(self, key):
        buf = BytesIO()
        self.s3.download_fileobj(self.bucket, key, buf)
        buf.seek(0)
        return buf

    def remove_law(self, slug):
        prefix = self._law_prefix(slug)
        keys = self._list_keys(prefix)
        if keys:
            # NB: `delete_objects` has a limit of 1000 keys, but we are not likely to run into that here.
            self.s3.delete_objects(Bucket=self.bucket, Delete={"Objects": keys})

    def create_or_replace_law(self, slug, download_url):
        self.remove_law(slug)

        response = requests.get(download_url)
        response.raise_for_status()

        zip_archive = zipfile.ZipFile(BytesIO(response.content))
        for filename in zip_archive.namelist():
            content_bytes = zip_archive.read(filename)
            self._upload_file(slug, filename, content_bytes)

        timestamp = _parse_last_modified_date_str(response)
        self._upload_file(slug, ".timestamp", timestamp)

    def list_slugs_with_timestamps(self):
        slugs = []
        paginated = self.s3.get_paginator("list_objects").paginate(Bucket=self.bucket, Prefix=self.key_prefix, Delimiter="/")

        for page in paginated:
            slugs += [
                obj["Prefix"].split("/")[-2]
                for obj in page.get("CommonPrefixes", [])
            ]

        slugs_with_timestamps = {}

        for slug in slugs:
            try:
                key = self._law_prefix(slug) + ".timestamp"
                timestamp = self._fetch_file(key).getvalue().decode()
            except botocore.exceptions.ClientError:
                print(f"Warning: No .timestamp for {slug}")
                timestamp = "00000000"
            slugs_with_timestamps[slug] = timestamp

        return slugs_with_timestamps

    def xml_file_for(self, slug):
        all_files = [obj["Key"] for obj in self._list_keys(self._law_prefix(slug))]
        xml_files = [f for f in all_files if f.endswith(".xml")]
        assert len(xml_files) == 1, f"Expected 1 XML file for {slug}, got {len(xml_files)}"

        return self._fetch_file(xml_files[0])
