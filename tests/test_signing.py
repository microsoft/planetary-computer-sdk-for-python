import os
import json
import unittest
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import warnings

import requests

import planetary_computer as pc
from planetary_computer.utils import parse_blob_url, is_fsspec_asset, parse_adlfs_url
from planetary_computer.sas import get_token, TOKEN_CACHE
from pystac import Asset, Item, ItemCollection
from pystac_client import ItemSearch


ACCOUNT_NAME = "naipeuwest"
CONTAINER_NAME = "naip"
TOKEN_REQUEST_URL = (
    "https://planetarycomputer.microsoft.com/api/sas/v1/token/naipeuwest/naip"
)

EXP_IMAGE = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.tif"
EXP_METADATA = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.txt"
EXP_THUMBNAIL = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/01.jpg"

SENTINEL_THUMBNAIL = (
    "https://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/10/T/ET/2020/10/02/"
    "S2B_MSIL2A_20201002T191229_N0212_R056_T10TET_20201004T193349.SAFE"
    "/GRANULE/L2A_T10TET_A018672_20201002T192031/QI_DATA/T10TET_20201002T191229_PVI.tif"
)

PC_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
HERE = Path(__file__).parent


def resolve(item: Item) -> Item:
    item.resolve_links()
    return item


def get_sample_item() -> Item:
    file_path = os.fspath(HERE.joinpath("data-files/sample-item.json"))
    return resolve(Item.from_file(file_path))


def get_sample_zarr_item() -> Item:
    file_path = os.fspath(HERE.joinpath("data-files/sample-zarr-item.json"))
    return resolve(Item.from_file(file_path))


def get_sample_zarr_open_dataset_item() -> Item:
    file_path = os.fspath(
        HERE.joinpath("data-files/sample-zarr-open-dataset-item.json")
    )
    return resolve(Item.from_file(file_path))


def get_sample_tabular_item() -> Item:
    file_path = os.fspath(HERE.joinpath("data-files/sample-tabular-item.json"))
    return resolve(Item.from_file(file_path))


def get_sample_item_collection() -> ItemCollection:
    return ItemCollection([get_sample_item()])


def get_sample_references() -> dict:
    with open(os.fspath(HERE.joinpath("data-files/sample-reference-file.json"))) as f:
        references = json.load(f)
    return references


class TestSigning(unittest.TestCase):
    def assertRootResolved(self, item: Item) -> None:
        root_link = item.get_root_link()
        self.assertIsNotNone(root_link)
        assert root_link  # for type checker
        self.assertTrue(root_link.is_resolved())

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

    def verify_asset_owner(self, signed_item: Item) -> None:
        for asset in signed_item.assets.values():
            self.assertIs(asset.owner, signed_item)

    def test_signed_assets(self) -> None:
        signed_item = pc.sign(get_sample_item())
        self.verify_signed_urls_in_item(signed_item)
        self.verify_asset_owner(signed_item)
        self.assertRootResolved(signed_item)

    def test_read_signed_asset(self) -> None:
        signed_href = pc.sign(SENTINEL_THUMBNAIL)
        r = requests.get(signed_href)
        self.assertEqual(r.status_code, 200)

    def test_signed_item_collection(self) -> None:
        signed_item_collection = pc.sign(get_sample_item_collection())
        self.assertEqual(len(list(signed_item_collection)), 1)
        for signed_item in signed_item_collection:
            self.verify_signed_urls_in_item(signed_item)
            self.assertRootResolved(signed_item)

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

    def test_sign_assets_deprecated(self) -> None:
        item = get_sample_item()
        with self.assertWarns(FutureWarning):
            pc.sign_assets(item)

    def test_public_api(self) -> None:
        item = get_sample_item()

        self.assertEqual(type(pc.sign(item)), type(pc.sign_item(item)))
        self.assertEqual(
            type(pc.sign(item.assets["image"])),
            type(pc.sign_asset(item.assets["image"])),
        )
        self.assertEqual(
            type(pc.sign(item.assets["image"].href)),
            type(pc.sign_url(item.assets["image"].href)),
        )

    def test_get_token(self) -> None:
        result = get_token(account_name=ACCOUNT_NAME, container_name=CONTAINER_NAME)
        self.assertIn(TOKEN_REQUEST_URL, TOKEN_CACHE)
        self.assertIsInstance(result.token, str)
        self.assertEqual(result.token, TOKEN_CACHE[TOKEN_REQUEST_URL].token)

        result2 = get_token(account_name=ACCOUNT_NAME, container_name=CONTAINER_NAME)
        self.assertIs(result, result2)

    def test_sign_zarr_item(self) -> None:
        item = get_sample_zarr_item()
        result = pc.sign(item)
        self.assertIn(
            "credential",
            result.assets["zarr-abfs"].extra_fields["xarray:storage_options"],
        )
        self.assertRootResolved(item)

    def test_sign_zarr_open_dataset_item(self) -> None:
        item = get_sample_zarr_open_dataset_item()
        result = pc.sign(item)
        self.assertIn(
            "credential",
            result.assets["zarr-abfs"].extra_fields["xarray:open_kwargs"][
                "storage_options"
            ],
        )
        self.assertRootResolved(item)

    def test_sign_zarr_open_dataset_nested_item(self) -> None:
        # nest inside backend_kwargs
        item = get_sample_zarr_open_dataset_item()
        extra_fields = item.assets["zarr-abfs"].extra_fields
        extra_fields["xarray:open_kwargs"]["backend_kwargs"][
            "storage_options"
        ] = extra_fields["xarray:open_kwargs"].pop("storage_options")

        result = pc.sign(item)
        self.assertIn(
            "credential",
            result.assets["zarr-abfs"].extra_fields["xarray:open_kwargs"][
                "backend_kwargs"
            ]["storage_options"],
        )
        self.assertRootResolved(item)

    def test_sign_tabular_item(self) -> None:
        item = get_sample_tabular_item()
        result = pc.sign(item)
        self.assertIn(
            "credential", result.assets["data"].extra_fields["table:storage_options"]
        )
        self.assertRootResolved(item)

    def test_sign_vrt(self) -> None:
        vrt_string = Path(HERE / "data-files/stacit.vrt").read_text()
        self.assertEqual(vrt_string.count("?st"), 0)
        result = pc.sign(vrt_string)
        self.assertGreater(result.count("?st"), 0)

    def test_sign_references_file(self) -> None:
        references = get_sample_references()
        result = pc.sign(references)
        for v in result["templates"].values():
            self.assertSigned(v)

    def test_sign_other_mapping_raises(self) -> None:
        with self.assertRaisesRegex(TypeError, "When providing a mapping"):
            pc.sign({"version": None})

        with self.assertRaisesRegex(TypeError, "When providing a mapping"):
            pc.sign({})

        with self.assertRaisesRegex(TypeError, "When providing a mapping"):
            pc.sign({"version": None, "templates": None, "refs": None, "extra": None})


class TestUtils(unittest.TestCase):
    def test_parse_adlfs_url(self) -> None:
        result = parse_adlfs_url("abfs://my-container/my/path.ext")
        self.assertEqual(result, "my-container")

        result = parse_adlfs_url("az://my-container/my/path.ext")
        self.assertEqual(result, "my-container")

        result = parse_adlfs_url("s3://my-container/my/path.ext")
        self.assertIsNone(result)

        result = parse_adlfs_url("https://planetarycomputer.microsoft.com")
        self.assertIsNone(result)

    def test_is_fsspec_url(self) -> None:
        asset = Asset(
            "adlfs://my-container/my/path.ext",
            extra_fields={"table:storage_options": {"account_name": "foo"}},
        )
        self.assertTrue(is_fsspec_asset(asset))

        asset = Asset(
            "adlfs://my-container/my/path.ext",
            extra_fields={"table:storage_options": {}},
        )
        self.assertFalse(is_fsspec_asset(asset))

        asset = Asset("adlfs://my-container/my/path.ext")
        self.assertFalse(is_fsspec_asset(asset))

        asset = Asset(
            "adlfs://my-container/my/path.ext",
            extra_fields={"xarray:storage_options": {"account_name": "foo"}},
        )
        self.assertTrue(is_fsspec_asset(asset))

        asset = Asset(
            "adlfs://my-container/my/path.ext",
            extra_fields={"xarray:storage_options": {}},
        )
        self.assertFalse(is_fsspec_asset(asset))

        asset = Asset("adlfs://my-container/my/path.ext")
        self.assertFalse(is_fsspec_asset(asset))
