import fsspec
import planetary_computer


class PCFileSystem(fsspec.AbstractFileSystem):
    """
    Planetary Computer filesystem for fsspec.

    This file system is solely a convenience for automatically
    signing assets in fsspec URLs. It uses fsspec's
    `URL chaining <https://filesystem-spec.readthedocs.io/en/latest/features.html#url-chaining>`_
    and :meth:`planetary_computer.sign` to transform URLs like
    ``pc://https://<account>.blob.core.windows.net/container/asset`` to the signed version.

    Parameters
    ----------
    target_protocol : str
        The protocol used to load the actual asset (e.g. 'https')
    target_options : dict
        Additional keywords to use for the target protocol's fsspec filesystem
    fo: str, optional
        The target path.

    Examples
    --------
    This example loads a Kerchunk index file from Azure Blob Storage. The index file is in a private blob
    storage container and so needs to be signed. The ``pc`` in the URL will automatically sign the
    asset before attempting to load it.
    
    >>> import xarray as xr
    >>> url = "reference::pc::https://deltaresreservoirssa.blob.core.windows.net/references/reservoirs/CHIRPS.json"
    >>> result = xr.open_dataset(url, engine="zarr", consolidated=False)
    <xarray.Dataset>
    Dimensions:      (time: 13515, GrandID: 2951, ksathorfrac: 5)
    Coordinates:
      * GrandID      (GrandID) float64 nan nan nan nan nan ... nan nan nan nan nan
      * ksathorfrac  (ksathorfrac) float64 5.0 20.0 50.0 100.0 250.0
      * time         (time) datetime64[ns] NaT NaT NaT NaT NaT ... NaT NaT NaT NaT
    Data variables: (12/14)
        ETa          (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        Ea_res       (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        FracFull     (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        Melt         (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        P            (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        PET          (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        ...           ...
        Qout_res     (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        S_res        (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        Snow         (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        Temp         (time, GrandID, ksathorfrac) float32 dask.array<chunksize=(1, 2951, 5), meta=np.ndarray>
        latitude     (GrandID) float32 dask.array<chunksize=(2951,), meta=np.ndarray>
        longitude    (GrandID) float32 dask.array<chunksize=(2951,), meta=np.ndarray>
    """
    def __init__(
        self,
        target_protocol=None,
        target_options=None,
        fo=None,
        **kwargs,
    ):
        self.target_protocol = target_protocol
        self.target_options = target_options
        if fo:
            fo = planetary_computer.sign(fo)
        self.fo = fo
        self.target_fs = fsspec.filesystem(self.target_protocol, **self.target_options)
        if isinstance(self.target_fs, fsspec.implementations.reference.ReferenceFileSystem):
            # this is a hack, but we need to sign the references after they've been loaded.
            # for k, v in self.target_fs.templates.items():
            #     print(k, v)
            #     # print(k)
            #     self.target_fs.templates[k] = planetary_computer.sign(v)

            # ReferenceFileSystem.__init__ does some processing, which means this is too late.
            for k, v in self.target_fs.references.items():
                if isinstance(v, list) and len(v) == 3:
                    # print("sign", k)
                    self.target_fs.references[k] = [planetary_computer.sign(v[0]),] + v[1:]

        super().__init__(**kwargs)

    def open(self, path, mode="rb", block_size=None, cache_options=None, **kwargs):
        # print("open", path)
        if self.fo:
            path = self.fo
        return self.target_fs.open(path, mode=mode, block_size=block_size, cache_options=cache_options, **kwargs)

    def ls(self, path, detail=True, **kwargs):
        # print("ls", path)
        return self.target_fs.ls(path, detail=detail, **kwargs)
