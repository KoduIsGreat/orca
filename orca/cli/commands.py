#!/usr/bin/python3

from orca.core.config import process_config, OrcaConfig
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
    Run a workflow.
    """
    conf = process_config(file)
    print('process run ' + json.dumps(conf, indent=2))
    config = OrcaConfig(conf, args)
    config.execute()

