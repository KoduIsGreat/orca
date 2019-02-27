#!/usr/bin/python3

from orca.core.config import OrcaConfig
from orca.core.handler import ExecutionHandler
from orca.core.handler import ValidationHandler
import click
import json


@click.group()
def orca():
    pass


@orca.command()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(file, verbose, args):
    """
    Run an orca job.
    """
    config = OrcaConfig.create(file, args)
    executor = ExecutionHandler()

    executor.handle(config)

@orca.command()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def validate(file, verbose, args):
    """
    Validate an orca job.
    """
    config = OrcaConfig.create(file, args)
    validator = ValidationHandler()

    validator.handle(config)
