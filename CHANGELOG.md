# 0.3.0

## New Features

* `sign` now works on strings, `pystac.Item`, `pystac.Asset`, `pystac.ItemCollection`, and `pystac_client.ItemSearch` instances.
* Added top-level methods `sign_item`, `sign_asset`, and `sign_item_collection` to directly sign objects of those types.

## Deprecations

* `sign_assets` is deprecated. Use `sign_item` instead.

## Bug Fixes

* `sign_item` now handles items with assets containing links to files outside of blob storage by returning the asset unchanged. 