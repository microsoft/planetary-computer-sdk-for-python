from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel, Field
import pystac
from pystac.utils import datetime_to_str
import requests


from planetary_computer.utils import parse_blob_url
from planetary_computer.settings import Settings


class SASBase(BaseModel):
    """Base model for responses. Include expiry, use RFC339 datetime"""

    expiry: datetime = Field(alias="msft:expiry")

    class Config:
        json_encoders = {datetime: datetime_to_str}
        allow_population_by_field_name = True


class SignedLink(SASBase):
    """Signed SAS URL response"""

    href: str


class SASToken(SASBase):
    """SAS Token response"""

    token: str

    def sign(self, href: str) -> SignedLink:
        """Signs an href with this token"""
        return SignedLink(href=f"{href}?{self.token}", expiry=self.expiry)

    def ttl(self) -> float:
        """Number of seconds the token is still valid for"""
        return (self.expiry - datetime.now(timezone.utc)).total_seconds()


# Cache of signing requests so we can reuse them
# Key is the signing URL, value is the SAS token
TOKEN_CACHE: Dict[str, SASToken] = {}


def sign(unsigned_url: str) -> SignedLink:
    """Sign a blob URL

    Parameters
    ----------
    unsigned_url: str
        URL to a blob that need to be signed

    Returns
    -------
    The signed URL
    """
    settings = Settings.get()
    account, container = parse_blob_url(unsigned_url)
    signing_url = f"{settings.sas_url}/{account}/{container}"
    token = TOKEN_CACHE.get(signing_url)

    # Refresh the token if there's less than a minute remaining,
    # in order to give a small amount of buffer
    if not token or token.ttl() < 60:
        headers = (
            {"Ocp-Apim-Subscription-Key": settings.subscription_key}
            if settings.subscription_key
            else None
        )
        response = requests.get(signing_url, headers=headers)
        response.raise_for_status()
        token = SASToken(**response.json())
        if not token:
            raise ValueError(f"No token found in response: {response.json()}")
        TOKEN_CACHE[signing_url] = token
    return token.sign(unsigned_url)


def sign_assets(unsigned_item: pystac.Item) -> pystac.Item:
    """Sign all assets within a PySTAC item

    Parameters
    ----------
    unsigned_item : pystac.Item
        The PySTAC item containing assets that need to be signed

    Returns
    -------
    A new copy of the PySTAC item where all assets have been signed
    """
    signed_item = unsigned_item.clone()
    for key in signed_item.assets:
        signed_item.assets[key].href = sign(signed_item.assets[key].href).href
    return signed_item
