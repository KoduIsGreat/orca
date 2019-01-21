import unittest
from orca.config import find_config
from orca.config import OrcaConfig
import os

fixture_path = os.path.dirname(__file__)
class OrcaConfigTest(unittest.TestCase):

    def test_find_config(self):
        path = os.path.join(fixture_path,'fixtures','test.yml')
        config = find_config(path)
        assert config != None

    def test_build_client_map(self):
        path = os.path.join(fixture_path,'fixtures','test.yml')
        config = find_config(path)
        orca_config = OrcaConfig(config)
        assert orca_config != None
    
    def test_excute_config(self):
        path = os.path.join(fixture_path,'fixtures','test.yml')
        config = find_config(path)
        orca_config = OrcaConfig(config)
        responses = orca_config.execute()

        assert responses != None
        assert len(responses) == 1

if __name__ == '__main__': unittest.main()