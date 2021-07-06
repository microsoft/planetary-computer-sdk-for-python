import os
import json
from typing import Any, Dict
import unittest
from urllib.parse import parse_qs, urlparse
import warnings

import requests

import planetary_computer as pc
from planetary_computer.utils import parse_blob_url
from pystac import Item, ItemCollection
from pystac_client import ItemSearch


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

PC_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"


def get_sample_item_dict() -> Dict[str, Any]:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data-files/sample-item.json")
    )
    with open(file_path) as json_file:
        return json.load(json_file)


def get_sample_item() -> Item:
    return Item.from_dict(get_sample_item_dict())


def get_sample_item_collection() -> ItemCollection:
    return ItemCollection([get_sample_item()])


class TestSigning(unittest.TestCase):
    def assertSigned(self, url: str) -> None:
        # Ensure the signed item has an "se" URL parameter added to it,
        # which indicates it has been signed
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        self.assertIsNotNone(query_params["se"])

    def test_parse_blob_url(self) -> None:
        account, container = parse_blob_url(urlparse(EXP_IMAGE))
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

    def verify_signed_urls_in_item(self, signed_item: Item) -> None:
        for key in ["image", "metadata", "thumbnail"]:
            signed_url = signed_item.assets[key].href
            self.assertSigned(signed_url)

    def test_signed_assets(self) -> None:
        signed_item = pc.sign(get_sample_item())
        self.verify_signed_urls_in_item(signed_item)

    def test_read_signed_asset(self) -> None:
        signed_href = pc.sign(SENTINEL_THUMBNAIL)
        r = requests.get(signed_href)
        self.assertEqual(r.status_code, 200)

    def test_signed_item_collection(self) -> None:
        signed_item_collection = pc.sign(get_sample_item_collection())
        self.assertEqual(len(list(signed_item_collection)), 1)
        for signed_item in signed_item_collection:
            self.verify_signed_urls_in_item(signed_item)

    def test_search_and_sign(self) -> None:
        # Filter out a resource warning coming from within the pystac-client search
        warnings.simplefilter("ignore", ResourceWarning)

        search = ItemSearch(
            url=PC_SEARCH_URL,
            bbox=(-73.21, 43.99, -73.12, 44.05),
            collections=CONTAINER_NAME,
            limit=1,
            max_items=1,
        )
        signed_item_collection = pc.sign(search)
        self.assertEqual(len(list(signed_item_collection)), 1)
        for signed_item in signed_item_collection:
            self.verify_signed_urls_in_item(signed_item)
