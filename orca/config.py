import yaml
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)
def find_config(filename="orca.yml"):
    file = os.path.join(os.getcwd(),filename)
    current_working_path = Path(file)
    relative_path = Path(filename)
    if current_working_path.exists():
        try:
            return process_config(current_working_path)
        except OrcaConfigException as e:
            log.error(e)
    elif relative_path.exists():
        try:
            return process_config(relative_path)
        except OrcaConfigException as e:
            log.error(e)


def process_config(filename):
    with open(filename,'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as e:
            log.error(e)
            raise OrcaConfigException("error loading, maybe use -f")

def validate_config(config):

    return True

class OrcaConfigException(Exception):
    pass

class OrcaConfig(object):

    def __init__(self, config):
        self.services = config.services
        self.steps = config.steps
        self.forks = config.forks
