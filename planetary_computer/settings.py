from typing import Optional
import pydantic

SETTINGS_ENV_FILE = "~/.planetarycomputer/settings.env"
SETTINGS_ENV_PREFIX = "PC_SDK_"

DEFAULT_SAS_TOKEN_ENDPOINT = "https://planetarycomputer.microsoft.com/api/sas/v1/token"


class Settings(pydantic.BaseSettings):
    """PC SDK configuration settings

    Settings defined here are attempted to be read in two ways, in this order:
      * environment variables
      * environment file: ~/.planetarycomputer/settings.env

    That is, any settings defined via environment variables will take precedence
    over settings defined in the environment file, so can be used to override.

    All settings are prefixed with `PC_SDK_`
    """

    # PC_SDK_SUBSCRIPTION_KEY: subscription key to send along with token
    # requests. If present, allows less restricted rate limiting.
    subscription_key: Optional[str] = None

    # PC_SDK_SAS_URL: The planetary computer SAS endpoint URL.
    # This will default to the main planetary computer endpoint.
    sas_url: str = DEFAULT_SAS_TOKEN_ENDPOINT

    class Config:
        env_file = SETTINGS_ENV_FILE
        env_prefix = SETTINGS_ENV_PREFIX
