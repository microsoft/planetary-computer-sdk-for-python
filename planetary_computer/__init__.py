"""Planetary Computer"""

import copy
from typing import Dict, Tuple
from urllib.parse import urlparse

import requests
import pystac

from .models import SASToken, SignedLink
from .settings import Settings

# Cache of signing requests so we can reuse them
# Key is the signing URL, value is the SAS token
TOKEN_CACHE: Dict[str, SASToken] = {}

SETTINGS = Settings()


def parse_blob_url(url: str) -> Tuple[str, str]:
    """Find the account and container in a blob URL

    Parameters
    ----------
    url: str
        URL to extract information from

    Returns
    -------
    Tuple of the account name and container name
    """
    try:
        parsed_url = urlparse(url.rstrip("/"))
        account_name = parsed_url.netloc.split(".")[0]
        path_blob = parsed_url.path.lstrip("/").split("/", 1)
        container_name = path_blob[-2]
    except Exception as failed_parse:
        raise ValueError(f"Invalid blob URL: {url}") from failed_parse

    return account_name, container_name


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
    account, container = parse_blob_url(unsigned_url)
    signing_url = f"{SETTINGS.sas_url}/{account}/{container}"
    token = TOKEN_CACHE.get(signing_url)

    # Refresh the token if there's less than a minute remaining,
    # in order to give a small amount of buffer
    if not token or token.ttl() < 60:
        headers = (
            {"Ocp-Apim-Subscription-Key": SETTINGS.subscription_key}
            if SETTINGS.subscription_key
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
    signed_item = copy.deepcopy(unsigned_item)
    for key in signed_item.assets:
        signed_item.assets[key].href = sign(signed_item.assets[key].href).href
    return signed_item
