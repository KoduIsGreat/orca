import unittest
from orca.core.config import OrcaConfig
from orca.core.handler import ExecutionHandler
from orca.core.handler import DotfileHandler

import os

fixture_path = os.path.dirname(__file__)

def get_config(file_name):
    path = os.path.join(fixture_path, 'fixtures', 'configs', file_name)
    with open(path, "r") as p:
      return OrcaConfig.create(p)

def print_workflow(file_name: str):
    handler = DotfileHandler()
    handler.handle(get_config(file_name))

class OrcaConfigTest(unittest.TestCase):

    def test_print_switch_task(self):
        print_workflow('switch.yaml')

    def test_print_for_task(self):
        print_workflow('for.yaml')

    def test_print_par_task(self):
        print_workflow('par.yaml')


if __name__ == '__main__': unittest.main()
