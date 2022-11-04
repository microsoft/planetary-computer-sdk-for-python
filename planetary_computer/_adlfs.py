import typing

from planetary_computer.sas import get_token

if typing.TYPE_CHECKING:
    import adlfs
    import azure.storage.blob


def get_container_client(
    account_name: str, container_name: str
) -> "azure.storage.blob.ContainerClient":
    """
    Get a :class:`azure.storage.blob.ContainerClient` with credentials.

    Args:
        account_name (str): The storage account name.
        container_name (str): The storage container name.
    Returns:
        The :class:`azure.storage.blob.ContainerClient` with the short-lived SAS token
        set as the credential.
    """
    try:
        import azure.storage.blob
    except ImportError as e:
        raise ImportError(
            "'planetary_computer.get_container_clinent' requires "
            "the optional dependency 'azure-storage-blob'."
        ) from e

    token = get_token(account_name, container_name).token
    return azure.storage.blob.ContainerClient(
        f"https://{account_name}.blob.core.windows.net",
        container_name,
        credential=token,
    )


def get_adlfs_filesystem(
    account_name: str, container_name: str
) -> "adlfs.AzureBlobFileSystem":
    """
    Get an :class:`adlfs.AzureBlobFileSystem` with credentials.

    Args:
        account_name (str): The storage account name.
        container_name (str): The storage container name.
    Returns:
        The :class:`adlfs.AzureBlobFileSystem` with the short-lived SAS token
        set as the credential.
    """
    try:
        import adlfs
    except ImportError as e:
        raise ImportError(
            "'planetary_computer.get_adlfs_filesystem' requires "
            "the optional dependency 'adlfs'."
        ) from e
    token = get_token(account_name, container_name).token
    fs = adlfs.AzureBlobFileSystem(account_name, credential=token)
    return fs
