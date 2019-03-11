import unittest
from orca.core.handler import DotfileHandler

from tests.util import run_handler


class DotFileHandlerTests(unittest.TestCase):

    def test_print_switch_task(self):
        run_handler('switch.yaml', DotfileHandler())

    def test_print_for_task(self):
        run_handler('for.yaml', DotfileHandler())

    def test_print_par_task(self):
        run_handler('par.yaml', DotfileHandler())


if __name__ == '__main__':
    unittest.main()
