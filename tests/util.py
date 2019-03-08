import os
from orca.core.config import OrcaConfig
from orca.core.handler import OrcaHandler

fixture_path = os.path.dirname(__file__)


def get_config(file_name):
    path = os.path.join(fixture_path, 'fixtures', 'configs', file_name)
    with open(path, "r") as p:
        return OrcaConfig.create(p)


def run_handler(file_name: str, handler: OrcaHandler):
    handler.handle(get_config(file_name))
