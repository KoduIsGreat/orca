from unittest import TestCase
from orca.core.config import OrcaConfig, OrcaConfigException  # noqa: F401

from tests.util import get_config

class OrcaSchemaTest(TestCase):
    pass

    def test_single_task(self):
        config = get_config('simple_example.yaml')
        assert config is not None

    # def test_duplicate_outputs(self):
    #
    #     with self.assertRaises(OrcaConfigException):
    #         config = get_config('duplicate_outputs.yaml')
