from click.testing import CliRunner
from orca.cli import commands
import unittest
from tests.util import get_config_path


class OrcaCommandTest(unittest.TestCase):

    def test_run(self):
        runner = CliRunner()
        runner.invoke(commands.run, [get_config_path('simple_example.yaml'), '--ledger-json=./test.json'])

    def test_version(self):
        runner = CliRunner()
        runner.invoke(commands.version)
