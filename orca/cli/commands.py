
import orca as o   # must be renamed
from orca.core.config import OrcaConfig
from orca.core.config import log
from orca.core.handler import ExecutionHandler
from orca.core.handler import ValidationHandler
from orca.core.handler import DotfileHandler
from orca.core.ledger import JSONFileLedger

import logging
import click
import click_log

click_log.basic_config(log)

@click.group()
@click_log.simple_verbosity_option(log, default='INFO')
def orca():
  pass


@orca.command()
def version():
  """
  Print the orca version.
  """
  print(o.__version__)
    
@orca.command()
@click.option('--json-ledger-file', type=click.Path())
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(json_ledger_file, file, args):
  """
  Run an orca workflow.
  """
  ledger = None
  if json_ledger_file:
    ledger = JSONFileLedger(json_ledger_file)
    
  config = OrcaConfig.create(file, args)
  executor = ExecutionHandler(ledger)
  executor.handle(config)


@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def validate(file, args):
  """
  Validate an orca workflow.
  """
  config = OrcaConfig.create(file, args)
  validator = ValidationHandler()
  validator.handle(config)


# Create a visual workflow:
#    $ python orca todot abc.yaml
#  will generate 'abc.dot' in the same folder of abc.yaml
#  convert this with the 'dot' command:
#    $ dot -Tpdf switch.dot -o switch.pdf
#    $ dot -Tpng switch.dot -o switch.png
#    $ dot -Tsvg switch.dot -o switch.svg

@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def todot(file, args):
  """
  Create a graphviz dot file from an orca workflow. 
  """
  config = OrcaConfig.create(file, args)
  printer = DotfileHandler()
  printer.handle(config)

