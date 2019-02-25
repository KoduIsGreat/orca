import unittest
from orca.core.config import process_config
from orca.core.config import OrcaConfig
import os

fixture_path = os.path.dirname(__file__)

def run_workflow(file_name: str):
    path = os.path.join(fixture_path, 'fixtures', 'configs', file_name)
    yaml = process_config(open(path, 'r'))
    config = OrcaConfig(yaml)
    config.execute()

class OrcaConfigTest(unittest.TestCase):

    def test_inline_bash_task(self):
        run_workflow('bash-inline.yaml')

    def test_csip_task(self):
        run_workflow('csip.yaml')

    def test_python_task(self):
        run_workflow('python.yaml')

    def test_fork_task(self):
        run_workflow('par.yaml')

    def test_for_task(self):
        run_workflow('for.yaml')

    def test_switch_task(self):
        run_workflow('switch.yaml')

if __name__ == '__main__': unittest.main()
