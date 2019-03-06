from unittest import TestCase
import os
from orca.core.config import OrcaConfig, OrcaConfigException

fixture_path = os.path.dirname(__file__)


def get_config(file_name):
    path = os.path.join(fixture_path, 'fixtures', 'schema', file_name)
    with open(path, "r") as p:
        return OrcaConfig.create(p)


class OrcaSchemaTest(TestCase):
    pass

    def test_single_task(self):
        config = get_config('simple_example.yaml')
        assert config is not None

    def test_duplicate_outputs(self):

        with self.assertRaises(OrcaConfigException):
            config = get_config('duplicate_outputs.yaml')
