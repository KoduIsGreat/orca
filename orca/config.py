import json
import logging
import yaml
import re
import importlib
from csip import Client
from typing import List, Dict, TextIO
# from docker.errors import APIError, TLSParameterError
# import docker
import os
from pandas import DataFrame
import requests
from dotted.collection import DottedCollection, DottedDict
log = logging.getLogger(__name__)

# this is temporary for demonstration purposes but should be replaced with api call to service registry
service_dict = {
    'csip.nwm': {
        'csip': 'http://ehs-csip-nwm.eastus.azurecontainer.io:8080/csip.nwm/d/netcdf/1.0'},
    'csip.temporal-aggregator': {
        'csip': 'http://localhost:8084/csip.temporal-aggregator/d/temporal/parameter/1.0'
    }
}


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


# all payload data during processing. must be global!
payload = DottedDict()
service = DottedDict()


class OrcaConfigException(Exception):
    pass


class OrcaConfig(object):

    def __init__(self, config: Dict, args: List[str] = None):
        self.conf = config.get('conf', {})
        self.resources = config.get('resources', {})
        self.deps = config.get('dependencies', {})
        self.vars = config.get('vars', {})
        self.workflow = config['workflow']
        self.__resolve_resouces()
        self.__resolve_dependencies()
        self.__set_vars(self.vars, args if args is not None else [])

    def __resolve_resouces(self):
        pass
        # client = docker.from_env()
        # if 'registry' in self.resources:
        #     try:
        #         registry = self.resources.get('registry')
        #         client.login(
        #             username=registry,
        #             password=os.environ['ORCA_DOCKER_REGISTRY_PASSWORD'],
        #             registry=registry)
        #     except (APIError, TLSParameterError) as e:
        #         raise OrcaConfigException(e)
        # self.__resolve_images()

    # def __resolve_images(self):
    #     client = docker.from_env()
    #
    #     containers = self.resources.get('containers')
    #     image_tags = list(map(lambda c: c['image'], containers))
    #     images = list(filter(lambda img: img.tags in image_tags, client.images.list()))
    #     if len(image_tags) == len(images):
    #         return images

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
            except Exception as e:
                raise OrcaConfigException(e)

    def __extract_csip_payload(self, client: Client) -> Dict:
        d = dict()
        for k,v in client.data.items():
            d[k] = v['value']
        return d

    def __build_csip_payload_step(self, name: str, service: Dict):
        payload_data = self.__extract_csip_payload(Client().get_capabilities(service.get('csip')))
        node_meta = 'payload ({0})'.format(name)
        return {node_meta: payload_data}

    def __build_csip_service_step(self, name: str, service: Dict):
        node_meta = 'service ({0})'.format(name)
        return {node_meta: {'csip': service.get('csip')}}

    def __init_service(self, name: str, service: Dict) -> Dict:

        if 'csip' in service:
            return {
                'payload': self.__build_csip_payload_step(name, service),
                'service': self.__build_csip_service_step(name, service)
            }

    def __init_sequence(self, sequence: Dict) -> None:
        new_sequence = list()
        for step in sequence:
            node = next(iter(step))
            print(" --- exploding step: '{}'".format(node))
            node_info = self.__get_node_info(node)
            meta = node_info['meta']
            node_type = node_info['type']
            if node_type == 'service':
                try:
                    payload_and_service = self.__init_service(meta, service_dict.get(meta))
                    new_sequence.append(payload_and_service.get('payload'))
                    new_sequence.append(payload_and_service.get('service'))
                except KeyError as e:
                    raise OrcaConfigException(e)
            else:
                raise OrcaConfigException('Invalid, Orca element to initalize')
        self.workflow = new_sequence

    def __handle_sequence(self, sequence: Dict) -> None:
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
            print("  handle props: {0} -> {1}".format(key, str(value)))
            payload[name + "." + key] = self.__resolve(value)

    def __handle_csip_result(self, client: Client, name:str) ->None:
        for k, v in client.data.items():
            print(" handling result props: {0} -> {1}".format(k, str(v)))
            service[name + "." + k] = v['value']

    def __handle_requests_result(self, response, name: str) -> None:
        for k,v in response.content:
            print(" handling req result props: {0} -> {1}".format(k, str(v)))
            service[name + "." + k] = v

    def __handle_csip_client(self, url: object, name: str) -> None:
        try:
            client = Client()
            for key, value in payload[name].items():
                if isinstance(value, DottedCollection):
                    client.add_data(key, value.to_python())
                else:
                    client.add_data(key, value)
            self.__handle_csip_result(client.execute(url), name)
        except requests.exceptions.HTTPError as e:
            raise OrcaConfigException(e)

    def __handle_requests_client(self, url: str, service: Dict, name: str) -> None:
        if 'method' not in service:
            raise OrcaConfigException("requests service operator must include method: service {0}".format(name))
        if service['method'] == 'GET':
            self.__handle_requests_result(requests.get(url, params=service['params']), name)
        elif service['method'] == 'POST':
            if isinstance(payload[name], DottedCollection):
                self.__handle_requests_result(requests.post(url, payload[name].to_python()), name)
            else:
                self.__handle_requests_result(requests.post(url,payload[name]), name)

    def __handle_file_client(self, path: str, name: str) -> None:
        pass

    def __handle_service(self, service: Dict, name: str) -> None:
        if 'file' in service:
            print("  calling local: " + name)
            _file = self.__resolve(service['file'])
            self.__handle_file_client(_file, name)
        elif 'csip' in service:
            # _url = self.__resolve(service['csip'])
            # log.info("  calling remote csip: " + _url)
            self.__handle_csip_client(service['csip'], name)
        elif 'url' in service:
            _url = self.__resolve(service['url'])
            log.info('calling remote url {0}', _url)
            self.__handle_requests_client(_url, service, name)

    def __handle_if(self, sequence:Dict, cond:str) -> None:
        if eval(cond):
            self.__handle_sequence(sequence)

    def __handle_while(self, sequence:Dict, cond:str) -> None:
        while eval(cond):
            self.__handle_sequence(sequence)

    def __create(self, name: str, description: str) -> Dict:
        return {
            'apiVersion': '1.0',
            'name': name,
            'description': description,
            'version': '0.1',
            'dependencies': self.deps,
            'conf': self.conf,
            'vars': self.vars,
            'workflow': self.workflow
        }
    def __output_data(self):
        fmt = self.conf.get('outputFormat', 'json')
        if fmt == 'json':
            with open('inputs.json', 'w') as json_ifile:
                json.dump(payload.to_python(), json_ifile, indent=2)
            with open('outputs.json', 'w') as json_ofile:
                json.dump(service.to_python(), json_ofile, indent=2)
        elif fmt == 'yaml' or fmt == 'yml':
            with open('inputs.yml', 'w') as yml_ifile:
                yaml.dump(payload.to_python(), yml_ifile, default_flow_style=False)
            with open('outputs.yml', 'w') as yml_ofile:
                yaml.dump(service.to_python(), yml_ofile, default_flow_style=False)
        elif fmt == 'csv':
            with open('inputs.csv', 'w') as csv_ifile:
                df = DataFrame.from_dict(payload.to_python())
                df.to_csv(csv_ifile)
            with open('outputs.csv', 'w') as csv_ofile:
                df = DataFrame.from_dict(service.to_python())
                df.to_csv(csv_ofile)
        else:
            raise OrcaConfigException("{0} format not yet supported".format(fmt))

    def execute(self) -> None:
        self.__handle_sequence(self.workflow)
        self.__output_data()
        print(payload)

    def init(self) -> None:
        self.__init_sequence(self.workflow)

    def write_config(self, name: str, description: str, fmt: str ='yml'):
        if fmt == 'yml' or fmt == 'yaml':
            with open(name+'.yml', 'w') as yml_file:
                yaml.dump(self.__create(name, description), yml_file, default_flow_style=False)
        elif fmt == 'json':
            with open(name+'.json', 'w') as json_file:
                json.dump(self.__create(name, description), json_file, indent=2)
        else:
            raise OrcaConfigException('{0} is not a supported workflow format'.format(fmt))
