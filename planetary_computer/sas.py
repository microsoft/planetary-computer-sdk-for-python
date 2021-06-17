from datetime import datetime, timezone
from typing import Dict, TypeVar

import requests
from pydantic import BaseModel, Field
from pystac import Asset, Item
from pystac.utils import datetime_to_str
from pystac_client import ItemCollection, ItemSearch

from planetary_computer.settings import Settings
from planetary_computer.utils import parse_blob_url


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

T = TypeVar("T", str, Asset, Item, ItemCollection)


def sign(obj: T) -> T:
    """
    Sign all relevant URLs within an object with a Shared Access (SAS)
    Token, which allows for read access.

    Parameters
    ----------
    obj (T): Any supported object containing one or more URLs to sign. Must be one of:
             str (a URL), Asset, Item, or ItemCollection

    Returns
    -------
    The object with all relevant URLs updated to include SAS Tokens
    """
    if isinstance(obj, str):
        link = sign_link(obj)
        return link.href

    if isinstance(obj, Item):
        return sign_item(obj)

    if isinstance(obj, Asset):
        return sign_asset(obj)

    if isinstance(obj, ItemCollection):
        return sign_item_collection(obj)

    raise TypeError("Invalid type, must be one of: str, Asset, Item, or ItemCollection")


def sign_link(url: str) -> SignedLink:
    """Sign a URL with a Shared Access (SAS) Token, which allows for read access.

    Args:
        url (str): The HREF of the asset in the format of a URL.
            This can be found on STAC Item's Asset 'href'
            value.

    Returns:
        SignedLink: An object that contains the signed HREF
        in the format of a URL and the expiry time, which
        is when the HREF will no longer permit read access.
    """
    settings = Settings.get()
    account, container = parse_blob_url(url)
    token_request_url = f"{settings.sas_url}/{account}/{container}"
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
    return token.sign(url)


def sign_item(item: Item) -> Item:
    """Sign all assets within a PySTAC item

    Args:
        item (Item): The Item whose assets that will be signed

    Returns:
        Item: A new copy of the Item where all assets' HREFs have
        been replaced with a signed version. In addition, a "msft:expiry"
        property is added to the Item properties indicating the earliest
        expiry time for any assets that were signed.
    """
    signed_item = item.clone()
    for key in signed_item.assets:
        signed_item.assets[key] = sign_asset(signed_item.assets[key])
    return signed_item


def sign_asset(asset: Asset) -> Asset:
    """Sign a PySTAC asset

    Args:
        asset (Asset): The Asset to sign

    Returns:
        Asset: A new copy of the Asset where the HREF is replaced with a
        signed version.
    """
    signed_asset = asset.clone()
    signed_asset.href = sign(signed_asset.href)
    return signed_asset


def sign_item_collection(item_collection: ItemCollection) -> ItemCollection:
    """Sign a PySTAC item collection

    Args:
        item_collection (ItemCollection): The ItemCollection whose assets will be signed

    Returns:
        ItemCollection: A new copy of the ItemCollection where all assets'
        HREFs for each item have been replaced with a signed version. In addition,
        a "msft:expiry" property is added to the Item properties indicating the
        earliest expiry time for any assets that were signed.
    """
    return ItemCollection.from_dict(
        {
            "type": "FeatureCollection",
            "features": [sign(item).to_dict() for item in item_collection],
        }
    )


def search_and_sign(search: ItemSearch) -> ItemCollection:
    """Perform a PySTAC Client search, and sign the resulting item collection

    Args:
        search (ItemSearch): The ItemSearch whose resulting item assets will be signed

    Returns:
        ItemCollection: The resulting ItemCollection of the search where all assets'
        HREFs for each item have been replaced with a signed version. In addition,
        a "msft:expiry" property is added to the Item properties indicating the
        earliest expiry time for any assets that were signed.
    """
    return sign(search.items_as_collection())
