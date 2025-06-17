from __future__ import annotations

from typing import TYPE_CHECKING

from planetary_computer.sas import get_token

if TYPE_CHECKING:
    import sys

    from obstore.store import (
        AzureConfig,
        AzureCredentialProvider,
        AzureSASToken,
        AzureStore,
        ClientConfig,
        RetryConfig,
    )

    if sys.version_info >= (3, 11):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


def get_obstore(  # type: ignore[misc] # overlap with kwargs
    account_name: str,
    container_name: str,
    *,
    prefix: str | None = None,
    config: AzureConfig | None = None,
    client_options: ClientConfig | None = None,
    retry_config: RetryConfig | None = None,
    credential_provider: AzureCredentialProvider | None = None,
    **kwargs: Unpack[AzureConfig],  # type: ignore # noqa
) -> AzureStore:
    try:
        import obstore
    except ImportError as e:
        raise ImportError(
            "'planetary_computer.get_obstore_store' requires "
            "the optional dependency 'obstore'."
        ) from e

    def default_credential_provider() -> AzureSASToken:
        token = get_token(account_name, container_name)
        return {
            "sas_token": token.token,
            "expires_at": token.expiry,
        }

    credential_provider = credential_provider or default_credential_provider

    return obstore.store.AzureStore(
        account_name=account_name,
        container_name=container_name,
        prefix=prefix,
        config=config,
        client_options=client_options,
        retry_config=retry_config,
        credential_provider=credential_provider,
        **kwargs,  # type: ignore # (container_name key overlaps with positional arg)
    )
