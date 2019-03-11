import unittest
from orca.core.handler import ExecutionHandler
from tests.util import run_handler


class OrcaExecutionTest(unittest.TestCase):

    def test_comprehensive_example(self):
        run_handler('datetime.yaml', ExecutionHandler())

    def test_inline_bash_task(self):
        run_handler('bash-inline.yaml', ExecutionHandler())

    def test_csip_task(self):
        run_handler('csip.yaml', ExecutionHandler())

    def test_fork_task(self):
        run_handler('par.yaml', ExecutionHandler())

    def test_for_task(self):
        run_handler('for.yaml', ExecutionHandler())

    def test_switch_task(self):
        run_handler('switch.yaml', ExecutionHandler())

    def test_var1_task(self):
        run_handler('var1.yaml', ExecutionHandler())

    def test_var2_task(self):
        run_handler('var2.yaml', ExecutionHandler())

    def test_var3_task(self):
        run_handler('var3.yaml', ExecutionHandler())

    def test_var4_task(self):
        run_handler('var4.yaml', ExecutionHandler())


if __name__ == '__main__':
    unittest.main()
