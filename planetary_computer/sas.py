import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Mapping, TypeVar, cast
import collections.abc
from copy import deepcopy
import warnings

from functools import singledispatch
from urllib.parse import urlparse, parse_qs
import requests
from pydantic import BaseModel, Field
from pystac import Asset, Item, ItemCollection, STACObjectType
from pystac.utils import datetime_to_str
from pystac.serialization.identify import identify_stac_object_type
from pystac_client import ItemSearch

from planetary_computer.settings import Settings
from planetary_computer.utils import (
    parse_blob_url,
    parse_adlfs_url,
    is_fsspec_asset,
    is_vrt_string,
    asset_xpr,
)


BLOB_STORAGE_DOMAIN = ".blob.core.windows.net"
AssetLike = TypeVar("AssetLike", Asset, Dict[str, Any])


class SASBase(BaseModel):
    """Base model for responses."""

    expiry: datetime = Field(alias="msft:expiry")
    """RFC339 datetime format of the time this token will expire"""

    class Config:
        json_encoders = {datetime: datetime_to_str}
        allow_population_by_field_name = True


class SignedLink(SASBase):
    """Signed SAS URL response"""

    href: str
    """The HREF in the format of a URL that can be used in HTTP GET operations"""


class SASToken(SASBase):
    """SAS Token response"""

    token: str
    """The Shared Access (SAS) Token that can be used to access the data
    in, for example, Azure's Python SDK"""

    def sign(self, href: str) -> SignedLink:
        """Signs an href with this token"""
        return SignedLink(href=f"{href}?{self.token}", expiry=self.expiry)

    def ttl(self) -> float:
        """Number of seconds the token is still valid for"""
        return (self.expiry - datetime.now(timezone.utc)).total_seconds()


# Cache of signing requests so we can reuse them
# Key is the signing URL, value is the SAS token
TOKEN_CACHE: Dict[str, SASToken] = {}


@singledispatch
def sign(obj: Any, copy: bool = True) -> Any:
    """Sign the relevant URLs belonging to any supported object with a
    Shared Access (SAS) Token, which allows for read access.

    Args:
        obj (Any): The object to sign. Must be one of:
            str (URL), Asset, Item, ItemCollection, or ItemSearch, or a mapping.
        copy (bool): Whether to sign the object in place, or make a copy.
            Has no effect for immutable objects like strings.
    Returns:
        Any: A copy of the object where all relevant URLs have been signed
    """
    raise TypeError(
        "Invalid type, must be one of: str, Asset, Item, ItemCollection, "
        "ItemSearch, or mapping"
    )


@sign.register(str)
def sign_string(url: str, copy: bool = True) -> str:
    """Sign a URL or VRT-like string containing URLs with a Shared Access (SAS) Token

    Signing with a SAS token allows read access to files in blob storage.

    Args:
        url (str): The HREF of the asset as a URL or a GDAL VRT

            Single URLs can be found on a STAC Item's Asset ``href`` value. Only URLs to
            assets in Azure Blob Storage are signed, other URLs are returned unmodified.

            GDAL VRTs can combine many data sources into a single mosaic. A VRT can be
            built quickly from the GDAL STACIT driver
            https://gdal.org/drivers/raster/stacit.html. Each URL to Azure Blob Storage
            within the VRT is signed.
        copy (bool): No effect.

    Returns:
        str: The signed HREF or VRT
    """
    if is_vrt_string(url):
        return sign_vrt_string(url)
    else:
        return sign_url(url)


def sign_url(url: str, copy: bool = True) -> str:
    """Sign a URL or with a Shared Access (SAS) Token

    Signing with a SAS token allows read access to files in blob storage.

    Args:
        url (str): The HREF of the asset as a URL

            Single URLs can be found on a STAC Item's Asset ``href`` value. Only URLs to
            assets in Azure Blob Storage are signed, other URLs are returned unmodified.
        copy (bool): No effect.

    Returns:
        str: The signed HREF
    """
    parsed_url = urlparse(url.rstrip("/"))
    if not parsed_url.netloc.endswith(BLOB_STORAGE_DOMAIN):
        return url

    parsed_qs = parse_qs(parsed_url.query)
    if set(parsed_qs) & {"st", "se", "sp"}:
        #  looks like we've already signed it
        return url

    account, container = parse_blob_url(parsed_url)
    token = get_token(account, container)
    return token.sign(url).href


def _repl_vrt(m: re.Match) -> str:
    # replace all blob-storages URLs with a signed version.
    return sign_url(m.string[slice(*m.span())])


def sign_vrt_string(vrt: str, copy: bool = True) -> str:
    """Sign a VRT-like string containing URLs with a Shared Access (SAS) Token

    Signing with a SAS token allows read access to files in blob storage.

    Args:
        vrt (str): The GDAL VRT

            GDAL VRTs can combine many data sources into a single mosaic. A VRT can be
            built quickly from the GDAL STACIT driver
            https://gdal.org/drivers/raster/stacit.html. Each URL to Azure Blob Storage
            within the VRT is signed.
        copy (bool): No effect.

    Returns:
        str: The signed VRT

    Examples
    --------
    >>> from osgeo import gdal
    >>> from pathlib import Path
    >>> search = (
    ...     "STACIT:\"https://planetarycomputer.microsoft.com/api/stac/v1/search?"
    ...     "collections=naip&bbox=-100,40,-99,41"
    ...     "&datetime=2019-01-01T00:00:00Z%2F..\":asset=image"
    ... )
    >>> gdal.Translate("out.vrt", search)
    >>> signed_vrt = planetary_computer.sign(Path("out.vrt").read_text())
    >>> print(signed_vrt)
    <VRTDataset rasterXSize="161196" rasterYSize="25023">
    ...
    </VRTDataset>
    """
    return asset_xpr.sub(_repl_vrt, vrt)


@sign.register(Item)
def sign_item(item: Item, copy: bool = True) -> Item:
    """Sign all assets within a PySTAC item

    Args:
        item (Item): The Item whose assets that will be signed
        copy (bool): Whether to copy (clone) the item or mutate it inplace.

    Returns:
        Item: An Item where all assets' HREFs have
        been replaced with a signed version. In addition, a "msft:expiry"
        property is added to the Item properties indicating the earliest
        expiry time for any assets that were signed.
    """
    if copy:
        item = item.clone()
    for key in item.assets:
        _sign_asset_in_place(item.assets[key])
    return item


@sign.register(Asset)
def sign_asset(asset: Asset, copy: bool = True) -> Asset:
    """Sign a PySTAC asset

    Args:
        asset (Asset): The Asset to sign
        copy (bool): Whether to copy (clone) the asset or mutate it inplace.

    Returns:
        Asset: An asset where the HREF is replaced with a
        signed version.
    """
    if copy:
        asset = asset.clone()
    return _sign_asset_in_place(asset)


def _sign_asset_in_place(asset: Asset) -> Asset:
    """Sign a PySTAC asset

    Args:
        asset (Asset): The Asset to sign in place

    Returns:
        Asset: Input Asset object modified in place: the HREF is replaced
        with a signed version.
    """
    asset.href = sign(asset.href)
    _sign_fsspec_asset_in_place(asset)
    return asset


def _sign_fsspec_asset_in_place(asset: AssetLike) -> None:
    if isinstance(asset, Asset):
        extra_d = asset.extra_fields
        href = asset.href
    else:
        extra_d = asset
        href = asset["href"]

    if is_fsspec_asset(extra_d):
        key: Optional[str]

        storage_options = None
        for key in ["table:storage_options", "xarray:storage_options"]:

            if key in extra_d:
                storage_options = extra_d[key]
                break
        if storage_options is None:
            storage_options = extra_d.get("xarray:open_kwargs", {}).get(
                "storage_options", None
            )

        if storage_options is None:
            storage_options = (
                extra_d.get("xarray:open_kwargs", {})
                .get("backend_kwargs", {})
                .get("storage_options", None)
            )

        if storage_options is None:
            return
        account = storage_options.get("account_name")
        container = parse_adlfs_url(href)
        if account and container:
            token = get_token(account, container)
            storage_options["credential"] = token.token


def sign_assets(item: Item) -> Item:
    warnings.warn(
        "'sign_assets' is deprecated and will be removed in a future version. Use "
        "'sign_item' instead.",
        FutureWarning,
        stacklevel=2,
    )
    return sign_item(item)


@sign.register(ItemCollection)
def sign_item_collection(
    item_collection: ItemCollection, copy: bool = True
) -> ItemCollection:
    """Sign a PySTAC item collection

    Args:
        item_collection (ItemCollection): The ItemCollection whose assets will be signed
        copy (bool): Whether to copy (clone) the ItemCollection or mutate it inplace.

    Returns:
        ItemCollection: An ItemCollection where all assets'
        HREFs for each item have been replaced with a signed version. In addition,
        a "msft:expiry" property is added to the Item properties indicating the
        earliest expiry time for any assets that were signed.
    """
    if copy:
        item_collection = item_collection.clone()
    for item in item_collection:
        for key in item.assets:
            _sign_asset_in_place(item.assets[key])
    return item_collection


@sign.register(ItemSearch)
def _search_and_sign(search: ItemSearch, copy: bool = True) -> ItemCollection:
    """Perform a PySTAC Client search, and sign the resulting item collection

    Args:
        search (ItemSearch): The ItemSearch whose resulting item assets will be signed
        copy (bool): No effect.

    Returns:
        ItemCollection: The resulting ItemCollection of the search where all assets'
        HREFs for each item have been replaced with a signed version. In addition,
        a "msft:expiry" property is added to the Item properties indicating the
        earliest expiry time for any assets that were signed.
    """
    return sign(search.get_all_items())


@sign.register(collections.abc.Mapping)
def sign_mapping(mapping: Mapping, copy: bool = True) -> Mapping:
    """
    Sign a mapping.

    Args:
        mapping (Mapping):

        The mapping (e.g. dictionary) to sign. This method can sign

            * Kerchunk-style references, which signs all URLs under the
              ``templates`` key. See https://fsspec.github.io/kerchunk/
              for more.
            * STAC items
            * STAC collections
            * STAC ItemCollections

        copy: Whether to copy (clone) the mapping or mutate it inplace.
    Returns:
        signed (Mapping): The dictionary, now with signed URLs.
    """
    if copy:
        mapping = deepcopy(mapping)

    if all(k in mapping for k in ["version", "templates", "refs"]):
        for k, v in mapping["templates"].items():
            mapping["templates"][k] = sign_url(v)

    elif (
        identify_stac_object_type(cast(Dict[str, Any], mapping)) == STACObjectType.ITEM
    ):
        for k, v in mapping["assets"].items():
            v["href"] = sign_url(v["href"])
            _sign_fsspec_asset_in_place(v)

    elif mapping.get("type") == "FeatureCollection" and mapping.get("features"):
        for feature in mapping["features"]:
            for k, v in feature.get("assets", {}).items():
                v["href"] = sign_url(v["href"])
                _sign_fsspec_asset_in_place(v)

    return mapping


sign_reference_file = sign_mapping


def get_token(account_name: str, container_name: str) -> SASToken:
    """
    Get a token for a container in a storage account.

    This will use a token from the cache if it's present and not too close
    to expiring. The generated token will be placed in the token cache.

    Args:
        account_name (str): The storage account name.
        container_name (str): The storage container name.
    Returns:
        SASToken: the generated token
    """
    settings = Settings.get()
    token_request_url = f"{settings.sas_url}/{account_name}/{container_name}"
    token = TOKEN_CACHE.get(token_request_url)

    # Refresh the token if there's less than a minute remaining,
    # in order to give a small amount of buffer
    if not token or token.ttl() < 60:
        headers = (
            {"Ocp-Apim-Subscription-Key": settings.subscription_key}
            if settings.subscription_key
            else None
        )
        response = requests.get(token_request_url, headers=headers)
        response.raise_for_status()
        token = SASToken(**response.json())
        if not token:
            raise ValueError(f"No token found in response: {response.json()}")
        TOKEN_CACHE[token_request_url] = token
    return token
