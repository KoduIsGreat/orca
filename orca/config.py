import json
import logging
import re
import sys
import importlib
import subprocess
import requests
import os

from csip import Client
from typing import List, Dict, TextIO
from ruamel import yaml
from concurrent.futures import ThreadPoolExecutor
# from docker.errors import APIError, TLSParameterError
# import docker
from pandas import DataFrame
from dotted.collection import DottedCollection, DottedDict


log = logging.getLogger(__name__)

# this is temporary for demonstration purposes but should be replaced with api call to service registry

# can we scrap this?
service_dict = {
    'csip.nwm': {
        'csip': 'http://ehs-csip-nwm.eastus.azurecontainer.io:8080/csip.nwm/d/netcdf/1.0'},
    'csip.temporal-aggregator': {
        'csip': 'http://localhost:8084/csip.temporal-aggregator/d/temporal/parameter/1.0'
    }
}

def process_config(file: TextIO) -> Dict:
    try:
        #config = yaml.load(file)
        #with open(file, "r") as myfile:
        data=file.read()
        print(data)
        
        # first pass: start with a valid the yaml file.
        yaml.load(data)
        
        # processing single quote string literals: " ' '
        repl = r"^(?P<key>\s*[^#:]*):\s+(?P<value>['].*['])\s*$"
        fixed_data = re.sub(repl, '\g<key>: "\g<value>"', data, flags=re.MULTILINE)
        print(fixed_data)
        
        # second pass: do it.
        config = yaml.load(fixed_data)

        #validate(config, schema)
        return config
    except yaml.YAMLError as e:
        log.error(e)
        raise OrcaConfigException("error loading yaml file.")

def run(cmd, errmsg="unspecified error", env = {}, delimiter='\n', exit_on_err=True, wd=None):
    #print(cmd)
    sp = subprocess.Popen(cmd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=wd)
    out, err = sp.communicate()
    if err:
        for line in err.split('\n'):
            print("ERROR: " + line)
    if sp.returncode != 0 and exit_on_err is True:
        print('ERROR: ' + str(sp.returncode) + " "   + errmsg)
    if out:
        o = ""
        for line in out.decode('utf-8').split(delimiter):
             if line:
                 o+=line + '\n'
        return o
    return None



class Service(object):

    def __init__(self, url: str,):
        self.url = url


# all payload data during processing. must be global!
payload = DottedDict()
task = DottedDict()
var = DottedDict()


class OrcaConfigException(Exception):
    pass

class OrcaConfig(object):

    def __init__(self, config: Dict, args: List[str] = None):
        self.conf = config.get('conf', {})
        self.deps = config.get('dependencies', [])
        self.vars = config.get('var', {})
        self.workflow = config['job']
        self.resources = config.get('resources', {})
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
                #globals().update(importlib.import_module(dep).__dict__)
                exec("import " + dep, globals())
            except OrcaConfigException as b:
                log.error("Orca could not resolve the {0} dependency".format(dep))

    def __resolve(self, value: object) -> object:
        """resolve the value against the globals"""
        #exec("global _tmp_\n_tmp_={}".format(value))
        #return eval("_tmp_")
        return eval(str(value))

    def __resolve_dict(self, dict: Dict) -> Dict:
        resolved = {key: self.__resolve(value) for key,value in dict.items()} 
        return resolved
    
    def __values_tostr(self, dict: Dict) -> Dict:
        a = {key: str(value) for key,value in dict.items()} 
        return a
      
    def __set_vars(self, vars: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        print(vars)
        for key, val in vars.items():
            try:
                if not key.isidentifier():
                    raise OrcaConfigException('Invalid variable identifier: "{0}"'.format(key))
                exec("var.{0}={1}".format(key,val))
                print("var.{0} = {1} -> {2}".format(key, str(val), str(eval("var."+key))))
            except Exception as e:
                raise

    def __extract_csip_payload(self, client: Client) -> Dict:
        d = {k:v['value'] for k,v in client.data.items() }
        return d

    def __build_csip_payload_step(self, name: str, task: Dict):
        payload_data = self.__extract_csip_payload(Client().get_capabilities(task.get('csip')))
        node_meta = 'payload ({0})'.format(name)
        return {node_meta: payload_data}

    def __build_task_step(self, name: str, task: Dict):
        node_meta = 'task ({0})'.format(name)
        return {node_meta: {'csip': task.get('csip')}}

    def __init_task(self, name: str, task: Dict) -> Dict:
        if 'csip' in task:
            return {
                'payload': self.__build_csip_payload_step(name, task),
                'service': self.__build_task_step(name, task)
            }

    def __init_sequence(self, sequence: Dict) -> None:
        new_sequence = list()
        for step in sequence:
            node = next(iter(step))
            print(" --- exploding step: '{}'".format(node))
            node_info = self.__get_node_info(node)
            meta = node_info['meta']
            node_type = node_info['type']
            if node_type == 'task':
                try:
                    payload_and_task = self.__init_task(meta, service_dict.get(meta))
                    new_sequence.append(payload_and_task.get('payload'))
                    new_sequence.append(payload_and_task.get('service'))
                except KeyError as e:
                    raise OrcaConfigException(e)
            else:
                raise OrcaConfigException('Invalid, Orca element to initalize')
        self.workflow = new_sequence
        
        
# Handler        

    def __handle_sequence(self, sequence: Dict) -> None:
        for step in sequence:
            node = next(iter(step))
            #if node == "payload":
                #self.__handle_payload(step[node], meta)
            if node == "task":
                print(" ---- task: '{}'".format(step['task']))
                self.__handle_task(step, step['task'])
            elif node.startswith("if "):
                print(" ---- if: '{}'".format(node[3:]))
                self.__handle_if(step[node], node[3:])
            elif node.startswith("for "):
                print(" ---- for: '{}'".format(node[4:]))
                self.__handle_for(step[node], node[4:])
            elif node == "fork":
                print(" ---- fork: ")
                self.__handle_fork(step[node])
            elif node.startswith("switch "):
                print(" ---- switch: '{}'".format(node[7:]))
                self.__handle_switch(step[node], node[7:])
            else:
                raise OrcaConfigException('Invalid step in job: "{0}"'.format(node))
        
    #def __handle_payload(self, payload_:Dict, name:str) -> None:
        #for key, value in payload_.items():
            #print("  handle props: {0} -> {1}".format(key, str(value)))
            #payload[name + "." + key] = self.__resolve(value)

    def __handle_csip_result(self, client: Client, name:str) ->None:
        for k, v in client.data.items():
            print(" handling result props: {0} -> {1}".format(k, str(v)))
            task[name + "." + k] = v['value']

    def __handle_requests_result(self, response, name: str) -> None:
        for k,v in response.content:
            print(" handling req result props: {0} -> {1}".format(k, str(v)))
            task[name + "." + k] = v

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

    def __handle_requests_client(self, url: str, task: Dict, name: str) -> None:
        if 'method' not in task:
            raise OrcaConfigException("requests service operator must include method: service {0}".format(name))
        if task['method'] == 'GET':
            self.__handle_requests_result(requests.get(url, params=task['params']), name)
        elif task['method'] == 'POST':
            if isinstance(payload[name], DottedCollection):
                self.__handle_requests_result(requests.post(url, payload[name].to_python()), name)
            else:
                self.__handle_requests_result(requests.post(url,payload[name]), name)

    def __handle_python_client(self, path: str, name: str) -> None:
        print("  exec python file : " + path)
        exec(open(path).read(), globals())

    def __handle_bash_client(self, path: str, name: str, env: Dict) -> None:
        out = run(path, env=env)
        print(out)

    def __handle_task(self, task: Dict, name: str) -> None:
        if not name.isidentifier():
            raise OrcaConfigException('Invalid task name, must be identifier: "{0}"'.format(name))

        inputs = {}
        if 'inputs' in task:
            inputs = self.__resolve_dict(task['inputs'])

        if 'python' in task:
            _file = self.__resolve(task['python'])
            print("  calling python: " + _file)
            self.__handle_python_client(_file, name)
        elif 'bash' in task:
            _file = task['bash']
            #_file = self.__resolve(task['bash'])
            print("  calling bash: " + _file)
            env = self.__values_tostr(inputs)
            self.__handle_bash_client(_file, name, env)
        elif 'csip' in task:
            # _url = self.__resolve(task['csip'])
            # log.info("  calling remote csip: " + _url)
            self.__handle_csip_client(task['csip'], name)
        elif 'http' in task:
            _url = self.__resolve(task['http'])
            log.info('calling remote url {0}', _url)
            self.__handle_requests_client(_url, task, name)

# control structures

    def __handle_if(self, sequence:Dict, cond:str) -> None:
        """Handle if."""
        if eval(cond, globals()):
            self.__handle_sequence(sequence)
            
    def __handle_switch(self, sequence:Dict, cond:str) -> None:
        """Handle conditional switch."""
        c = eval(cond, globals())
        #print(sequence)
        for case, seq in sequence.items():
            if c == case:
                self.__handle_sequence(seq)

    def __handle_for(self, sequence:Dict, var_expr:str) -> None:
        """Handle Looping"""
        i = var_expr.find(",")
        if i == -1:
            raise OrcaConfigException('Invalid for expression: "{0}"'.format(var_expr))
        var = var_expr[:i]
        if not var.isidentifier():
            raise OrcaConfigException('Not a valid identifier: "{0}"'.format(var))
        expr = var_expr[i+1:]
        for i in eval(expr, globals()):
            exec("{0}='{1}'".format(var,i), globals())
            self.__handle_sequence(sequence)

    def __handle_fork(self, sequence:Dict) -> None:
        """Handle parallel execution"""
        # get the sub workflows
        #print(sequence)
        with ThreadPoolExecutor(max_workers=(len(sequence)+1)) as executor:
            for workflows in sequence:
                #print(workflows)
                #self.__handle_sequence(workflows['workflow'])  # for testing as seq
                executor.submit(self.__handle_sequence, workflows)
    
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
