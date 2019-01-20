import unittest
from orca.config import find_config
import os

fixture_path = os.path.dirname(__file__)
class OrcaConfigTest(unittest.TestCase):

    def test_find_config(self):
        path = os.path.join(fixture_path,'fixtures','test.yml')
        config = find_config(path)
        assert config != None


if __name__ == '__main__': unittest.main()