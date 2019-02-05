import json
import logging
import os
import yaml
import re

from csip import Client
#from jsonschema import validate
#from orca.schema import schema
from typing import List, Dict, TextIO, Any
from dotted.collection import DottedCollection, DottedDict, DottedList

log = logging.getLogger(__name__)

def process_config(file: TextIO) -> Dict:
    try:
        config = yaml.load(file)
        #validate(config, schema)
        return config
    except yaml.YAMLError as e:
        log.error(e)
        raise OrcaConfigException("error loading yaml file.")


# all payload data during processing. must be global!
payload = DottedDict()   

class OrcaConfigException(Exception):
    pass
    
class OrcaConfig(object):

    def __init__(self, config: Dict, args: List[str]):
        self.workflow = config['workflow']
        self.__set_vars(config.get('vars',{}), args)
        #self.client_dict = self.__create_client_dict__(config)

    def _resolve(value: object) -> object:
        """resolve the value against the globals"""
        exec("global _tmp_\n_tmp_={}".format(value))
        return eval("_tmp_")

    def _get_node_info(node:str) -> Dict:
        """Split the step node into type and name/cond"""
        p = re.match(r'\s*(?P<type>\w*)\s*(\((?P<meta>.*?)\))?', node)
        return p.groupdict()

    def __set_vars(self, vars: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        for key,val in vars.items():
            exec("global {0}\n{0}={1}".format(key,val))
            print("var {0} = {1} -> {2}".format(key, str(val), str(eval(key))))
            
    def __handle_sequence(self, sequence:Dict) -> None:
        for step in sequence:
            node = next(iter(step))
            print(" --- step: '{}'".format(node))
            nodeinfo =  OrcaConfig._get_node_info(node)
            meta = nodeinfo['meta']
            nodetype = nodeinfo['type']
            if nodetype == "payload":
                self.__handle_payload(step[node], meta)
            elif nodetype == "service":
                self.__handle_service(step[node], meta)
            elif node.startswith("if "):
                self.__handle_if(step[node], node[3:])
            elif node.startswith("while "):
                self.__handle_while(step[node], node[6:])
            else:
                raise OrcaConfigException("Invalid workflow step: " + node)
        
    def __handle_payload(self, payload_:Dict, name:str) -> None:
        for key, value in payload_.items():
            print("  handle props: {0} -> {1}".format(key,str(value)));
            payload[name + "." + key] = OrcaConfig._resolve(value)
            
    def __handle_service(self, service:Dict, name:str) -> None:
        if 'file' in service:
            print("  calling local: " + name)
        elif 'url' in service:
            _url = OrcaConfig._resolve(service['url'])
            print("  calling remote: " + _url)
                
    def __handle_if(self, sequence:Dict, cond:str) -> None:
        if eval(cond):
            self.__handle_sequence(sequence)

    def __handle_while(self, sequence:Dict, cond:str) -> None:
        while eval(cond):
            self.__handle_sequence(sequence)
                           
    def execute(self) -> None:
        self.__handle_sequence(self.workflow)
        print(payload)
        
    #def __create_client_dict__(self, config : Dict):
        #dict = collections.OrderedDict()
        #for step in config['steps']:
            #url = to_url(step['service'])
            #config_items = step['config']
            #catalog = Client.get_catalog(url)
            #service_url = catalog[0].metainfo['service_url']
            #client = Client()
            #for item in config_items:
                #client.add_data(item['name'],item['value'])
            #dict[service_url] = client
        #return dict

    #def execute(self):
        #responses = list()
        #for url in self.client_dict.keys():
            #client = self.client_dict[url]
            #response = client.execute(url)
            #responses.append(response)
            #print(response)
        #return responses
