from unittest import TestCase
from orca.core.config import OrcaConfig, OrcaConfigException  # noqa: F401

from tests.util import get_config

class OrcaSchemaTest(TestCase):
    pass

    def test_single_task(self):
        config = get_config('simple_example.yaml')
        assert config is not None

    def test_for_schema(self):
        config = get_config('for.yaml')
        assert config is not None

    def test_if_task_schema(self):
        config = get_config('if.yaml')
        assert config is not None

    def test_fork_task_schema(self):
        config = get_config('par.yaml')
        assert config is not None

    def test_switch_schema(self):
        config = get_config('switch.yaml')
        assert config is not None

    def test_duplicate_outputs(self):
        with self.assertRaises(OrcaConfigException):
            config = get_config('duplicate_outputs.yaml')
            assert config is not None
