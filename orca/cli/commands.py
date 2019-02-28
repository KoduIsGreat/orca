
import orca as o
from orca.core.config import OrcaConfig
from orca.core.config import log
from orca.core.handler import ExecutionHandler
from orca.core.handler import ValidationHandler
from orca.core.handler import DotfileHandler

import logging
import click
import click_log

click_log.basic_config(log)
loglevel = 'INFO'

@click.group()
@click_log.simple_verbosity_option(log, default=loglevel)
def orca():
    pass


@orca.command()
def version():
    """
    Print the orca version.
    """
    print(o.__version__)
    
@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(file, args):
    """
    Run an orca workflow
    """
    config = OrcaConfig.create(file, args)
    executor = ExecutionHandler()
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


@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def todot(file, args):
    """
    Create a dot file from an orca workflow.
    """
    config = OrcaConfig.create(file, args)
    printer = DotfileHandler()
    printer.handle(config)

