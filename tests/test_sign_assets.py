import os
import json
import unittest
from urllib.parse import parse_qs, urlparse

import requests

import planetary_computer as pc
from planetary_computer.utils import parse_blob_url
import pystac


ACCOUNT_NAME = "naipeuwest"
CONTAINER_NAME = "naip"

EXP_IMAGE = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.tif"
EXP_METADATA = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.txt"
EXP_THUMBNAIL = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.jpg"

SENTINEL_THUMBNAIL = (
    "https://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/10/T/ET/2020/10/02/"
    "S2B_MSIL2A_20201002T191229_N0212_R056_T10TET_20201004T193349.SAFE"
    "/GRANULE/L2A_T10TET_A018672_20201002T192031/QI_DATA/T10TET_20201002T191229_PVI.tif"
)


def get_sample_item() -> pystac.Item:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data-files/sample-item.json")
    )
    with open(file_path) as json_file:
        item_dict = json.load(json_file)
    return pystac.Item.from_dict(item_dict)


class TestSignAssests(unittest.TestCase):
    def assertSigned(self, url: str) -> None:
        # Ensure the signed item has an "se" URL parameter added to it,
        # which indicates it has been signed
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        self.assertIsNotNone(query_params["se"])

    def test_parse_blob_url(self) -> None:
        account, container = parse_blob_url(EXP_IMAGE)
        self.assertEqual(ACCOUNT_NAME, account)
        self.assertEqual(CONTAINER_NAME, container)

    def test_signed_url(self) -> None:
        self.assertSigned(pc.sign(EXP_IMAGE))

    def test_unsigned_assets(self) -> None:
        item = get_sample_item()

        # Simple test to ensure the sample image has the data we're expecting
        self.assertEqual(EXP_IMAGE, item.assets["image"].href)
        self.assertEqual(EXP_METADATA, item.assets["metadata"].href)
        self.assertEqual(EXP_THUMBNAIL, item.assets["thumbnail"].href)

    def test_signed_assets(self) -> None:
        unsigned_item = get_sample_item()
        signed_item = pc.sign_assets(unsigned_item)

        # Ensure the original item wasn't mutated, and all URLs are signed
        for key in ["image", "metadata", "thumbnail"]:
            signed_url = signed_item.assets[key].href
            self.assertNotEqual(unsigned_item.assets[key].href, signed_url)
            self.assertSigned(signed_url)

    def test_read_signed_asset(self) -> None:
        signed_href = pc.sign(SENTINEL_THUMBNAIL)
        r = requests.get(signed_href)
        self.assertEqual(r.status_code, 200)
