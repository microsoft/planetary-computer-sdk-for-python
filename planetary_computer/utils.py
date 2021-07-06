from typing import Tuple
from urllib.parse import ParseResult, urlunparse


def parse_blob_url(parsed_url: ParseResult) -> Tuple[str, str]:
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
        account_name = parsed_url.netloc.split(".")[0]
        path_blob = parsed_url.path.lstrip("/").split("/", 1)
        container_name = path_blob[-2]
    except Exception as failed_parse:
        raise ValueError(
            f"Invalid blob URL: {urlunparse(parsed_url)}"
        ) from failed_parse

    return account_name, container_name
