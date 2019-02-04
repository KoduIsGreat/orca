from orca.config import process_config, OrcaConfig
import click
import json

@click.group()
def orca():
    pass

@orca.command()
def pull(**kwargs):
    print('called pull')

@orca.command()
def validate(**kwargs):
    find_config()

@orca.command()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(file, verbose, args):
    """Run a workflow."""
    a = process_config(file)
    print('process run ' + json.dumps(a, indent=2))
    config = OrcaConfig(a, args)
    config.execute()
