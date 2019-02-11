import json
import logging
import yaml
import re
import importlib
from csip import Client
from typing import List, Dict, TextIO

import requests
from dotted.collection import DottedCollection, DottedDict
log = logging.getLogger(__name__)


def process_config(file: TextIO) -> Dict:
    try:
        config = yaml.load(file)
        #validate(config, schema)
        return config
    except yaml.YAMLError as e:
        log.error(e)
        raise OrcaConfigException("error loading yaml file.")


class Service(object):

    def __init__(self, url: str,):
        self.url = url

class OrcaConfigFactory(object):

    def __init__(self, services: List[Service]):
        self.services = services
        self.config: Dict = dict()
    
    def __build_meta(self, name: str, description: str, version: str):
        self.config['name'] = name
        self.config['description'] = description
        self.config['version'] = version

    def __build_conf(self):
        self.config['conf'] = {'trace': 'file.txt'}

    def __build_var_stub(self):
        self.config['vars'] = dict()

    def __extract_payload(self, csip_response: Dict) -> Dict:
        return csip_response

    def __extract_csip_payload(self, client: Client):
        data = dict()
        for key, value in client.data:
            print("key {0} = {1} ".format(key, str(value)))

    def __build_workflow(self):
        client = Client()
        steps: List = list()
        for service in self.services:
            response = client.get_capabilities(service.url).data
            steps.append({'payload': self.__extract_payload(response)})
            steps.append({'service': {'url': service.url}})
        self.config['workflow'] = steps

    def create(self, name: str, description:str, version:str):
        self.config.clear()
        self.__build_meta(name, description, version)
        self.__build_conf()
        self.__build_var_stub()
        self.__build_workflow()
        return OrcaConfig(self.config)
 

# all payload data during processing. must be global!
payload = DottedDict()
service = DottedDict()


class OrcaConfigException(Exception):
    pass


class OrcaConfig(object):

    def __init__(self, config: Dict, args: List[str] = None):
        self.conf = config.get('conf', {})
        self.deps = config.get('dependencies', {})
        self.workflow = config['workflow']
        self.__resolve_dependencies()
        self.__set_vars(config.get('vars', {}), args if args is not None else [])

    def __resolve_dependencies(self):
        for dep in self.deps:
            try:
                globals().update(importlib.import_module(dep).__dict__)
            except OrcaConfigException as e:
                log.error("Orca could not resolve the {0} dependency".format(dep))


    def __resolve(self, value: object) -> object:
        """resolve the value against the globals"""
        exec("global _tmp_\n_tmp_={}".format(value))
        return eval("_tmp_")

    def __get_node_info(self, node:str) -> Dict:
        """Split the step node into type and name/cond"""
        p = re.match(r'\s*(?P<type>\w*)\s*(\((?P<meta>.*?)\))?', node)
        return p.groupdict()

    def __set_vars(self, vars: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        for key, val in vars.items():
            try:
                exec("global {0}\n{0}={1}".format(key,val))
                print("var {0} = {1} -> {2}".format(key, str(val), str(eval(key))))
            except IndexError:
                msg = "Invalid argument position for key {0} and value {1}".format(key,val)
                raise OrcaConfigException(msg)
            
    def __handle_sequence(self, sequence:Dict) -> None:
        for step in sequence:
            node = next(iter(step))
            print(" --- step: '{}'".format(node))
            nodeinfo = self.__get_node_info(node)
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
            print("  handle props: {0} -> {1}".format(key,str(value)))
            payload[name + "." + key] = self.__resolve(value)

    def __handle_csip_result(self, client: Client, name:str) ->None:
        for k, v in client.data.items():
            print(" handling result props: {0} -> {1}".format(k, str(v)))
            service[name + "." + k] = v['value']

    def __handle_requests_result(self, response, name:str) -> None:
        for k,v in response.content:
            print(" handling req result props: {0} -> {1}".format(k, str(v)))
            service[name + "." + k] = v

    def __handle_csip_client(self, url: object, name: str) -> None:
        client = Client()
        for key, value in  payload[name].items():
            if isinstance(value, DottedCollection):
                client.add_data(key,value.to_python())
            else:
                client.add_data(key,value)
        self.__handle_csip_result(client.execute(url), name)

    def __handle_requests_client(self, url:str, serv:Dict, name:str) -> None:
        if 'method' not in serv:
            raise OrcaConfigException("requests service operator must include method: service {0}".format(name))
        if serv['method'] == 'GET':
            self.__handle_requests_result(requests.get(url,params=serv['params']), name)
        elif serv['method'] == 'POST':
            self.__handle_requests_result(requests.post(url, payload[name]), name)

    def __handle_file_client(self, path:str, name:str) -> None:
        pass

    def __handle_service(self, serv:Dict, name:str) -> None:
        if 'file' in serv:
            print("  calling local: " + name)
            _file = self.__resolve(serv['file'])
            self.__handle_file_client(_file, name)
        elif 'csip' in serv:
            _url = self.__resolve(serv['csip'])
            log.info("  calling remote csip: " + _url)
            self.__handle_csip_client(_url,name)
        elif 'url' in serv:
            _url = self.__resolve(serv['url'])
            log.info('calling remote url {0}', _url)
            self.__handle_requests_client(_url, name)


    def __handle_if(self, sequence:Dict, cond:str) -> None:
        if eval(cond):
            self.__handle_sequence(sequence)

    def __handle_while(self, sequence:Dict, cond:str) -> None:
        while eval(cond):
            self.__handle_sequence(sequence)
                           
    def execute(self) -> None:
        self.__handle_sequence(self.workflow)
        print(payload)

    def write_config(self, fmt: str ='yaml'):
        if fmt == 'yaml':
            with open('read_after_write_test.yml', 'w') as yaml_file:
                yaml.dump(self.config, yaml_file, default_flow_style=False)
        elif fmt == 'json':
            with open('orca.json', 'w') as json_file:
                json.dump(self.config, json_file)