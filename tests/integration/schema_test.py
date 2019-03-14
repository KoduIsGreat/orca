from unittest import TestCase
from orca.core.errors import ConfigurationError
from tests.util import get_config


class OrcaSchemaTest(TestCase):
    pass

    def test_single_task(self):
        config = get_config('simple_example.yaml')
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

    def test_for_schema(self):
        config = get_config('for.yaml')
        assert config is not None

    def test_duplicate_kinds(self):
        with self.assertRaises(ConfigurationError) as e:
            config = get_config('duplicate_kinds.yaml')
            assert config is not None
            print(e)

    def test_duplicate_outputs(self):
        with self.assertRaises(ConfigurationError) as e:

            config = get_config('duplicate_outputs.yaml')
            assert config is not None
            print(e)

    def test_nested_dups(self):
        with self.assertRaises(ConfigurationError) as e:
            config = get_config('nested_duplicates.yaml')
            assert config is not None
            print(e)

    def test_missing_api_version(self):
        with self.assertRaises(ConfigurationError):
            config = get_config('missing_api_version.yaml')
            assert config is not None

    def test_missing_api_version(self):
        with self.assertRaises(ConfigurationError):
            config = get_config('invalid_api_version.yaml')
            assert config is not None
