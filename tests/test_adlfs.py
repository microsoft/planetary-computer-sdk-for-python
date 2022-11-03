import sys
from typing import Any

import azure.storage.blob
import pytest

import planetary_computer


def test_get_adlfs_filesystem_raises(monkeypatch: Any) -> None:
    monkeypatch.setitem(sys.modules, "adlfs", None)
    with pytest.raises(ImportError):
        planetary_computer.get_adlfs_filesystem("nrel", "oedi")


def test_get_adlfs_filesystem() -> None:
    fs = planetary_computer.get_adlfs_filesystem("nrel", "oedi")
    assert fs.account_url == "https://nrel.blob.core.windows.net"
    assert fs.credential is not None


def test_get_container_client() -> None:
    cc = planetary_computer.get_container_client("nrel", "oedi")
    assert cc.primary_endpoint.startswith("https://nrel.blob.core.windows.net/oedi")
    assert isinstance(cc, azure.storage.blob.ContainerClient)
