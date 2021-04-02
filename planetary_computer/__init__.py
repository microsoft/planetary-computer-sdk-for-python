"""Planetary Computer"""


def sign_assets(pystac_item: int) -> str:
    """Sign all assets within a PySTAC item:

    Parameters
    ----------
    pystac_item : pystac.Item
        The PySTAC item containing assets that need to be signed

    Returns
    -------
    A new copy of the PySTAC item where all assets have been signed
    """

    print(f"called sign_assets with: {pystac_item}")
    return f"TODO: {pystac_item}"
