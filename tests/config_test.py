import unittest
from orca.config import process_config
from orca.config import OrcaConfig
import os

fixture_path = os.path.dirname(__file__)


class OrcaConfigTest(unittest.TestCase):

    def test_find_config(self):
        path = os.path.join(fixture_path, 'fixtures', 'test.yml')
        config = process_config(path)
        assert config is not None


    def test_write_config(self):
        path = os.path.join(fixture_path, 'fixtures', 'write_test.yml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.write_config()

    def test_comprehensive(self):
        path = os.path.join(fixture_path, 'fixtures', 'comprehensive_example.yaml')
        yaml = process_config(open(path,'r'))
        config = OrcaConfig(yaml)
        assert config is not None
        config.execute()


if __name__ == '__main__': unittest.main()
