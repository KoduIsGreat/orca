import unittest
from orca.config import find_config

class OrcaConfigTest(unittest.TestCase):

    def test_find_config(self):
        config = find_config('fixtures/test.yml')
        assert config != None


if __name__ == '__main__': unittest.main()