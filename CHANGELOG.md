# 1.0.0

## Bug fixes

* Compatibility with `pydantic>=2.0` (https://github.com/microsoft/planetary-computer-sdk-for-python/pull/59)

## API Breaking Changes

* `planetary_computer.settings.Settings()` is no longer a pydantic Model. To support both pydantic 1.x and 2.x,
  the implementation of `Settings` changed. There aren't any user-facing changes in the primary API exposed by
  `Settings`, around creating the settings object and getting / setting values. But it no longer subclasses
  `pydantic.BaseModel`  (https://github.com/microsoft/planetary-computer-sdk-for-python/pull/59).

# 0.5.1

## Bug fixes

* Fixed rety mechanism

# 0.4.9

## Bug fixes

* Fixed `ImportError` when the optional dependency `azure-storage-blob` isn't installed.

# 0.4.8

## New Features

* `sign` now automatically retries failed HTTP requests.
* Added a convenience method `planetary_computer.get_container_client` for getting an authenticated ``azure.storage.blob.ContainerClient``.
* Added a convenience method `planetary_computer.get_adlfs_filesystem` for getting an authenticated ``adlfs.AzureBlobFileSystem``.

# 0.4.7

## New Features

* `sign` now supports signing URLs that have already been signed.
* `sign` now supports signing raw JSON objects, in addition to `pystac` objects.
* `sign` now supports signing `Collection` objects.
* Added a `sign_inplace` method for signing by directly mutating objects, rather than copying.

# 0.4.6

## New Features

* `sign` will now sign assets whose URLs are registered with [adlfs] and nest `storage_options` from the [xarray-assets] extension under `xarray:open_kwargs`.

# 0.4.5

## New Features

* `sign` will now sign [Kerchunk](kerchunk)-style dictionaries of references.

# 0.4.4

## New Features

* `sign` will now sign VRT-like strings, like those returned by GDAL's [STACIT](https://gdal.org/drivers/raster/stacit.html) driver.

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
[kerchunk]: https://fsspec.github.io/kerchunk/
