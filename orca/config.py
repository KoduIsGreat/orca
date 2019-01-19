import yaml
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)
def find_config(filename="orca.yml"):
    file = os.path.join(os.getcwd(),filename)
    current_working_path = Path(file)

    if current_working_path.exists():
        with open(file,'r') as stream:
            try:
                config = yaml.safe_load(stream)
                return config
            except yaml.YAMLError as e:
                log.error(e)
                raise OrcaConfigException("Could not find orca.yml, maybe use -f")


def validate_config(config):

    return True

class OrcaConfigException(Exception):
    pass

class OrcaConfig(object):

    def __init__(self, config):
        self.services = config.services
        self.steps = config.steps
        self.forks = config.forks
