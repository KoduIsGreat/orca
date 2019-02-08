from orca.config import process_config, OrcaConfig, OrcaConfigFactory, Service
import click
import json

@click.group()
def orca():
    pass

@orca.command()
def init():
    urls = input("List url's of services that you wish to create a workflow for separated by comma:\n")
    url_array = urls.split(',')
    print(url_array)
    services = [Service(url) for url in url_array]
    factory = OrcaConfigFactory( services)
    name = input("Name of Workflow: ")
    description = input("Description of workflow: ")
    version = input("Version of workflow: ")
    config = OrcaConfig(factory.create(name, description, version))
    config.write_config()

@orca.command()
def pull(**kwargs):
    print('called pull')


@orca.command()
def validate(**kwargs):
    pass


@orca.command()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('file', type=click.File('r'))
@click.argument('args', nargs=-1)
def run(file, verbose, args):
    """Run a workflow."""
    config = process_config(file)
    print('process run ' + json.dumps(config, indent=2))
    config = OrcaConfig(config, args)
    config.execute()
