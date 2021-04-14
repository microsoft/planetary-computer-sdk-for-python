import os
import unittest

import planetary_computer as pc
from planetary_computer.settings import SETTINGS_ENV_PREFIX, Settings


class TestSettings(unittest.TestCase):
    def test_reads_env_var(self) -> None:
        key_env_var = f"{SETTINGS_ENV_PREFIX}_SUBSCRIPTION_KEY"
        old_key = os.getenv(key_env_var)
        try:
            pc.set_subscription_key("PHILLY")
            self.assertEqual(Settings.get().subscription_key, "PHILLY")
        finally:
            if old_key:
                os.environ[key_env_var] = old_key
