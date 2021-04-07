import os
import json
import unittest
from urllib.parse import parse_qs, urlparse

import planetary_computer as pc
import pystac


ACCOUNT_NAME = "naipeuwest"
CONTAINER_NAME = "naip"

EXP_IMAGE = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.tif"
EXP_METADATA = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.txt"
EXP_THUMBNAIL = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.jpg"


def get_sample_item() -> pystac.Item:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data-files/sample-item.json")
    )
    with open(file_path) as json_file:
        item_dict = json.load(json_file)
    return pystac.Item.from_dict(item_dict)


class TestSignAssests(unittest.TestCase):
    def assertSignedUrl(self, signed_url: str) -> None:
        # Ensure the signed item has an "se" URL parameter added to it,
        # which indicates it has been signed
        parsed_url = urlparse(signed_url)
        query_params = parse_qs(parsed_url.query)
        self.assertIsNotNone(query_params["se"])

    def test_parse_blob_url(self) -> None:
        account, container = pc.parse_blob_url(EXP_IMAGE)
        self.assertEqual(ACCOUNT_NAME, account)
        self.assertEqual(CONTAINER_NAME, container)

    def test_signed_url(self) -> None:
        self.assertSignedUrl(pc.sign(EXP_IMAGE).href)

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
            self.assertSignedUrl(signed_url)
