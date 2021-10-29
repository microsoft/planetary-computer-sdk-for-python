# 0.4.3

## Bug Fixes

* Improved performance when using signed ItemCollections by not dropping the root link [#30][gh-30]

# 0.4.2

## New Features

* `sign` will now sign assets whose URLs are registered with [adlfs] and implement `xarray:storage_options` from the [xarray-assets] extension.


# 0.4.1

## Bug Fixes

* Fixed bug in `planetary_computer.sign(item)` returning items whose assets had no owner. [#25][gh-25]

# 0.4.0

## New Features

* `sign` will now sign assets whose URLs are registered with [adlfs] and implement `table:storage_options` from the [table] extension.

# 0.3.0

## New Features

* `sign` now works on strings, `pystac.Item`, `pystac.Asset`, `pystac.ItemCollection`, and `pystac_client.ItemSearch` instances.
* Added top-level methods `sign_item`, `sign_asset`, and `sign_item_collection` to directly sign objects of those types.

## Deprecations

* `sign_assets` is deprecated. Use `sign_item` instead.

## Bug Fixes

* `sign_item` now handles items with assets containing links to files outside of blob storage by returning the asset unchanged. 

[adlfs]: https://github.com/dask/adlfs
[table]: https://github.com/stac-extensions/table
[gh-25]: https://github.com/microsoft/planetary-computer-sdk-for-python/issues/25
[gh-30]: https://github.com/microsoft/planetary-computer-sdk-for-python/pull/30
[xarray-assets]: https://github.com/stac-extensions/xarray-assets
