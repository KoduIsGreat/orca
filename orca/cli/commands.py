#!/usr/bin/python3

from orca.config import process_config, OrcaConfig
import click
import json


@click.group()
def orca():
    pass

@orca.command()
@click.argument('file', type=click.File('r'))
@click.argument('name', type=click.STRING)
@click.argument('description', type=click.STRING)
@click.option('--format', type=click.Choice(['json', 'yml']))
def init(file, name, description, format):
    """
    Initialize a workflow from a services file
    """
    format = 'yml' if format is None else 'json'
    config = process_config(file)
    orca_config = OrcaConfig(config)
    orca_config.init()
    orca_config.write_config(name, description, format)

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


# @orca.command()
# @click.group()
# def service():
#     pass
#
# @service.command()
# def ls():
#     pass

