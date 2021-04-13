import pydantic


class Settings(pydantic.BaseSettings):
    """PC SDK configuration settings

    Settings defined here are attempted to be read in two ways, in this order:
      * environment variables
      * environment file: ~/.planetarycomputer/settings.env

    That is, any settings defined via environment variables will take precendence
    over settings defined in the environment file, so can be used to override.

    All settings are prefixed with `PC_SDK_`
    """

    # PC_SDK_SUBSCRIPTION_KEY: subcription key to send along with token
    # requests. If present, allows less restricted rate limiting.
    subscription_key: str

    class Config:
        env_file = "~/.planetarycomputer/settings.env"
        env_prefix = "PC_SDK_"
