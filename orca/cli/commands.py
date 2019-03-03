
import orca as o   # must be renamed
from orca.core.config import OrcaConfig, OrcaException, log
from orca.core.handler import ExecutionHandler
from orca.core.handler import ValidationHandler
from orca.core.handler import DotfileHandler
from orca.core.ledger import JSONFileLedger
from orca.core.ledger import MongoLedger

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
    
    
    
    

def check_format(ctx, param, value):
  if value is None:
    return
  c = value.split('/')
  if len(c) != 3:
    log.error("Invalid mongo connect string, expected '<host[:port]>/<db>/<col>'")
    ctx.exit()
  return c


# run a workflow:    
# python3 orca run --ledger-json /tmp/f.json for.yaml
# python3 orca run --ledger-mongo localhost/orcadb1/ledgercol for.yaml
#
# maybe import file into a db:
# mongoimport --db orca --collection ledger --file /tmp/f.json

@orca.command()
@click.option('--ledger-json', type=click.Path(), help='file ledger.')
@click.option('--ledger-mongo', type=str, 
              help='mongodb ledger, TEXT format "<host[:port]>/<db>/<col>".', callback=check_format)
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(ledger_json, ledger_mongo, file, args):
  """
  Run an orca workflow.
  """
  try:

    ledger = None
    if ledger_json:
      ledger = JSONFileLedger(ledger_json)
    elif ledger_mongo:
      ledger = MongoLedger(ledger_mongo)
    
    config = OrcaConfig.create(file, args)
    executor = ExecutionHandler(ledger)
    executor.handle(config)
  except OrcaException as e:
    log.error(e)



@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def validate(file, args):
  """
  Validate an orca workflow.
  """
  try:
    config = OrcaConfig.create(file, args)
    validator = ValidationHandler()
    validator.handle(config)
  except OrcaException as e:
    log.error(e)


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
  try:
    config = OrcaConfig.create(file, args)
    printer = DotfileHandler()
    printer.handle(config)
  except OrcaException as e:
    log.error(e)

