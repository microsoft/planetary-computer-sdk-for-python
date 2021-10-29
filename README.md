# Planetary Computer SDK for Python

Python library for interacting with the Microsoft Planetary Computer.

For general questions or discussions about the Planetary Computer, use the [microsoft/PlanetaryComputer](http://github.com/microsoft/PlanetaryComputer) repository.

## Installation

```python
pip install planetary-computer
```

If you have an API subscription key, you may provide it to the library by using the included configuration CLI:

```bash
planetarycomputer configure
```

Alternatively, a subscription key may be provided by specifying it in the `PC_SDK_SUBSCRIPTION_KEY` environment variable. A subcription key is not required for interacting with the service, however having one in place allows for less restricted rate limiting.


## Development

The following steps may be followed in order to develop locally:

```bash
## Create and activate venv
python3 -m venv env
source env/bin/activate

## Install requirements
python3 -m pip install -r requirements-dev.txt

## Install locally
pip install -e .

## Format code
./scripts/format

## Run tests
./scripts/test
```


## Usage

This library currently assists with signing Azure Blob Storage URLs. The `sign` function operates directly on an HREF string, as well as several [PySTAC](https://github.com/stac-utils/pystac) objects: `Asset`, `Item`, and `ItemCollection`. In addition, the `sign` function accepts a [STAC API Client](https://github.com/stac-utils/pystac-client) `ItemSearch`, which performs a search and returns the resulting `ItemCollection` with all assets signed. The following example demonstrates these use cases:

```python
from pystac import Asset, Item, ItemCollection
from pystac_client import ItemSearch
import planetary_computer as pc


# The sign function may be called directly on the Item
raw_item: Item = ...
item: Item = pc.sign(raw_item)
# Now use the item however you want. All appropriate assets are signed for read access.

# The sign function also works with an Asset
raw_asset: Asset = raw_item.assets['SR_B4']
asset = pc.sign(raw_asset)

# The sign function also works with an HREF
raw_href: str = raw_asset.href
href = pc.sign(raw_href)

# The sign function also works with an ItemCollection
raw_item_collection = ItemCollection([raw_item])
item_collection = pc.sign(raw_item_collection)

# The sign function also accepts an ItemSearch, and signs the resulting ItemCollection
search = ItemSearch(
    url=...,
    bbox=...,
    collections=...,
    limit=...,
    max_items=...,
)
signed_item_collection = pc.sign(search)
```


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
