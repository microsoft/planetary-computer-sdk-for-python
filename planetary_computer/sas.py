from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel, Field
import pystac
from pystac.utils import datetime_to_str
import requests


from planetary_computer.utils import parse_blob_url
from planetary_computer.settings import Settings


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


def sign(url: str) -> str:
    """Sign a URL with a Shared Access (SAS)
    Token, which allows for read access.

    Parameters
    ----------
    url (str): The HREF of the asset in the format of a URL.
        This can be found on STAC Item's Asset 'href' value.

    Returns
    -------
    The signed HREF that permits read access to the asset.
    """
    link = sign_link(url)
    return link.href


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


def sign_assets(item: pystac.Item) -> pystac.Item:
    """Sign all assets within a PySTAC item

    Args:
        item (pystac.Item): The Item whose assets that will be signed

    Returns:
        pystac.Item: A new copy of the Item where all assets HREFs have
        been replaced with a signed version. In addition, a "msft:expiry"
        property is added to the Item properties indicating the earliest
        expiry time for any assets that were signed.
    """
    signed_item = item.clone()
    for key in signed_item.assets:
        signed_item.assets[key].href = sign(signed_item.assets[key].href)
    return signed_item
