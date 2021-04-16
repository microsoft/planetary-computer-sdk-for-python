# Planetary Computer SDK for Python

Python library for interacting with the Microsoft Planetary Computer.

## Installation

```python
pip install planetarycomputer
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

This library currently assists with signing Azure Blob Storage URLs, both within PySTAC assets, and by providing raw URLs. The following examples demonstrate both of these use cases:

```python
import pystac
import planetary_computer as pc

raw_item: pystac.Item = ...
item: pystac.Item = pc.sign_assets(raw_item)

# Now use the item however you want. All appropriate assets are signed for read access.
```

```python
import planetary_computer as pc
import pystac

item: pystac.Item = ...  # Landsat item

b4_href = pc.sign(item.assets['SR_B4'].href)

with rasterio.open(b4_href) as ds:
   ...
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
