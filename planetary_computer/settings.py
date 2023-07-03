import os
from functools import lru_cache
from typing import Optional, TypeVar
import dataclasses


SETTINGS_ENV_FILE = "~/.planetarycomputer/settings.env"
SETTINGS_ENV_PREFIX = "PC_SDK_"

DEFAULT_SAS_TOKEN_ENDPOINT = "https://planetarycomputer.microsoft.com/api/sas/v1/token"


def set_subscription_key(key: str) -> None:
    """Sets the Planetary Computer API subscription key to use
    within the process that loaded this module. Ths does not write
    to the settings file.

    Args:
      key: The Planetary Computer API subscription key to use
        for methods inside this library that can utilize the key,
        such as SAS token generation.
    """
    Settings.get().subscription_key = key



def _from_env(key: str) -> Optional[str]:
    import dotenv
    value = os.environ.get(key)
    if value is None:
        dotenv.load_dotenv(os.path.expanduser(SETTINGS_ENV_FILE))
        value = os.environ.get(key)
    return value


def _subscription_key_default() -> Optional[str]:
    return _from_env("PC_SDK_SUBSCRIPTION_KEY")

def _sas_url_default() -> str:
    return _from_env("PC_SDK_SAS_URL") or DEFAULT_SAS_TOKEN_ENDPOINT


@dataclasses.dataclass
class Settings:
    subscription_key: Optional[str] = dataclasses.field(default_factory=_subscription_key_default)
    sas_url: Optional[str] = dataclasses.field(default_factory=_sas_url_default)

    @staticmethod
    @lru_cache(maxsize=1)
    def get() -> "Settings":
        return Settings()
