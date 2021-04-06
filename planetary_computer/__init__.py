"""Planetary Computer"""

import copy
from datetime import datetime, timezone
from typing import Dict, Tuple
from urllib.parse import parse_qs, urlparse

import dateutil.parser
import requests

import pystac


SAS_TOKEN_ENDPOINT = "https://planetarycomputer.microsoft.com/data/v1/token"

# Cache of signing requests so we can reuse them
# Key is the signing URL, value is the SAS token
TOKEN_CACHE: Dict[str, str] = {}


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


def token_expired(token: str) -> bool:
    """Determines whether or not a token has expired

    Parameters
    ----------
    token: str
        SAS token to determine expiration

    Returns
    -------
    True if expired, False if still valid
    """
    try:
        # The first part of the fake URL isn't important, just need to create
        # a URL to be able to parse the token, which is a set of URL params
        parsed_url = urlparse(f"http://example.com?{token}")
        query_params = parse_qs(parsed_url.query)
        expiration = dateutil.parser.parse(query_params["se"][0])
        now = datetime.now(timezone.utc)
        seconds_remaining = (expiration - now).total_seconds()
        # Consider the token expired if there's less than a minute remaining,
        # just to give a small amount of buffer
        return seconds_remaining < 60
    except Exception as failed_parse:
        raise ValueError(f"Invalid token: {token}") from failed_parse


def sign(unsigned_url: str) -> str:
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
    signing_url = f"{SAS_TOKEN_ENDPOINT}/{account}/{container}"
    token = TOKEN_CACHE.get(signing_url)

    if not token or token_expired(token):
        response = requests.get(signing_url)
        response.raise_for_status()
        print(f"resp: {response.json()}")

        token = response.json()["token"]
        if not token:
            raise ValueError(f"No token found in response: {response.json()}")
        TOKEN_CACHE[signing_url] = token
    return f"{unsigned_url}?{token}"


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
        signed_item.assets[key].href = sign(signed_item.assets[key].href)
    return signed_item
