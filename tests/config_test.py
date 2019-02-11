import unittest
from orca.config import process_config
from orca.config import OrcaConfig, OrcaConfigFactory, Service
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

    def test_factory(self):
        services = [Service('http://ehs-csip-nwm.eastus.azurecontainer.io:8080/csip.nwm/d/netcdf/1.0'),
                    Service('http://52.151.240.97:8080/csip.temporal-aggregator/d/temporal/1.0')]
        factory = OrcaConfigFactory(services)
        config = factory.create('test', 'a test', '1.0')
        config.write_config( fmt='yaml')
        assert 4 == len(config.workflow)

    def test_comprehensive(self):
        path = os.path.join(fixture_path, 'fixtures', 'comprehensive_example.yaml')
        yaml = process_config(open(path,'r'))
        config = OrcaConfig(yaml)
        assert config is not None
        config.execute()


if __name__ == '__main__': unittest.main()
