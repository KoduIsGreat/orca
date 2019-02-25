import unittest
from orca.core.config import process_config
from orca.core.config import OrcaConfig
import os

fixture_path = os.path.dirname(__file__)


class OrcaConfigTest(unittest.TestCase):

    def test_inline_bash_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'bash-inline.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

    def test_csip_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'csip.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

    def test_python_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'python.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

    def test_fork_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'par.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

    def test_for_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'for.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

    def test_switch_task(self):
        path = os.path.join(fixture_path, 'fixtures', 'configs', 'switch.yaml')
        yaml = process_config(open(path, 'r'))
        config = OrcaConfig(yaml)
        config.execute()

if __name__ == '__main__': unittest.main()
