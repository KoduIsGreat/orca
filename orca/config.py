import json
import logging
import os
from pathlib import Path
from csip import Client
import yaml
from jsonschema import validate
import collections
from orca.schema import schema

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
            config = yaml.load(stream)
            validate(config, schema)
            return config
        except yaml.YAMLError as e:
            log.error(e)
            raise OrcaConfigException("error loading, maybe use -f")

class OrcaConfigException(Exception):
    pass


def to_url(service):
    url = service['host'] +":" +service['port'] +'/'+service['name']
    return "http://{}".format(url)

class OrcaConfig(object):

    def __init__(self, config):

        self.steps = config['steps']
        self.client_dict = self.__create_client_dict__(config)
    
    def __create_client_dict__(self, config):
        dict = collections.OrderedDict()
        for step in config['steps']:
            url = to_url(step['service'])
            config_items = step['config']
            catalog = Client.get_catalog(url)
            service_url = catalog[0].metainfo['service_url']
            client = Client()
            for item in config_items:
                client.add_data(item['name'],item['value'])
            dict[service_url] = client
        return dict

    def execute(self):
        responses = list()
        for url in self.client_dict.keys():
            client = self.client_dict[url]
            response = client.execute(url)
            responses.append(response)
            print(response)
        return responses