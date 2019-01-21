from orca.config import find_config, OrcaConfig
import click

@click.group()
def orca():
    pass

@orca.command()
def pull(**kwargs):
    print('called pull')

@orca.command()
def validate(**kwargs):
    print('called validate')

@orca.command()
def run(**kwargs):
    config = OrcaConfig(find_config())
    config.execute()