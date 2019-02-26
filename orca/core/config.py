import json
import logging
import re
import os
from typing import List, Dict, TextIO
from ruamel import yaml
from concurrent.futures import ThreadPoolExecutor
from dotted.collection import DottedDict
from orca.core.tasks import OrcaTask, handle_http, handle_csip, handle_bash, handle_python
log = logging.getLogger(__name__)

# all payload data during processing. must be global!
task = DottedDict()
var = DottedDict()

def process_config(file: TextIO) -> Dict:
    try:
        data = file.read()
        print(data)
        
        # first pass: start with a valid the yaml file.
        yaml.load(data)
        
        # processing single quote string literals: " ' '
        repl = r"^(?P<key>\s*[^#:]*):\s+(?P<value>['].*['])\s*$"
        fixed_data = re.sub(repl, '\g<key>: "\g<value>"', data, flags=re.MULTILINE)
        print(fixed_data)
        
        # second pass: do it.
        config = yaml.load(fixed_data)

        return config
    except yaml.YAMLError as e:
        log.error(e)
        raise OrcaConfigException("error loading yaml file.")


class OrcaConfigException(Exception):
    pass


class OrcaConfig(object):
    
    def __init__(self, config: Dict, file: str = None, args: List[str] = None):
        self.file = file
        self.conf = config.get('conf', {})
        self.deps = config.get('dependencies', [])
        self.var = config.get('var', {})
        self.workflow = config['job']
        self.__resolve_dependencies()
        self.__set_vars({} if self.var is None else self.var, args if args is not None else [])
        
    def __get_yaml_dir(self) -> str:
        return os.path.dirname(self.file) if self.file is not None else "."

    def __resolve_dependencies(self):
        for dep in self.deps:
            try:
                exec("import " + dep, globals())
            except OrcaConfigException as b:
                log.error("Orca could not resolve the {0} dependency".format(dep))
      
    def __set_vars(self, variables: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        print(variables)
        for key, val in variables.items():
            try:
                if not key.isidentifier():
                    raise OrcaConfigException('Invalid variable identifier: "{0}"'.format(key))
                exec("var.{0}={1}".format(key,val))
                print("var.{0} = {1} -> {2}".format(key, str(val), str(eval("var."+key))))
            except Exception as e:
                raise e

    def __handle_sequence(self, sequence: Dict) -> None:
        for step in sequence:
            node = next(iter(step))
            if node == "task":
                print(" ---- task: '{}'".format(step['task']))
                self.__handle_task(step)
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

    def __select_handler(self, task_dict: Dict):
        if 'csip' in task_dict:
            return handle_csip
        elif 'http' in task_dict:
            return handle_http
        elif 'bash' in task_dict:
            return handle_bash
        elif 'python' in task_dict:
            return handle_python
        else:
            raise OrcaConfigException('Invalid task type: "{0}"'.format(task_dict))
            

    def __resolve_task_inputs(self, task_dict: Dict) -> Dict:
        inputs = task_dict.get('inputs',{})
        if inputs is not {}:
            for k, v in inputs.items():
                if str(v).startswith('task.') or str(v).startswith('var.'):
                    inputs[k] = eval(str(v), globals())
        return task_dict

    def __resolve_task(self, task_dict: Dict) -> Dict:
        for k, v in task_dict.items():
            if str(v).startswith('var.'):
                task_dict[k] = eval(str(v), globals())
        return self.__resolve_task_inputs(task_dict)

    def __handle_task(self, task_dict: Dict) -> None:
        handle = self.__select_handler(task_dict)
        resolved_task = self.__resolve_task(task_dict.copy())
        _task = OrcaTask(resolved_task)
        result = handle(_task, self.__get_yaml_dir())
        if isinstance(result, dict):
            for k, v in result.items():
                task[k] = v
        elif isinstance(result, str):
            print(result)

    # control structures
    def __handle_if(self, sequence:Dict, cond:str) -> None:
        """Handle if."""
        if eval(cond, globals()):
            self.__handle_sequence(sequence)
            
    def __handle_switch(self, sequence:Dict, cond:str) -> None:
        """Handle conditional switch."""
        c = eval(cond, globals())
        seq = sequence.get(c, sequence.get("default", None))
        if seq is not None:
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

    def __handle_fork(self, sequences:Dict) -> None:
        """Handle parallel execution"""
        #print(sequence)
        with ThreadPoolExecutor(max_workers=(len(sequences))) as executor:
            for sequence in sequences:
                #print(workflows)
                #self.__handle_sequence(sequence)  # for testing as seq
                executor.submit(self.__handle_sequence, sequence)

    def __create(self, name: str, description: str) -> Dict:
        return {
            'apiVersion': "orca/'1.0'",
            'name': name,
            'description': description,
            'version': '0.1',
            'dependencies': self.deps,
            'conf': self.conf,
            'var': self.var,
            'job': self.job
        }

    def execute(self) -> None:
        self.__handle_sequence(self.workflow)
        print(task)

    def write_config(self, name: str, description: str, fmt: str ='yml'):
        if fmt == 'yml' or fmt == 'yaml':
            with open(name+'.yml', 'w') as yml_file:
                yaml.dump(self.__create(name, description), yml_file, default_flow_style=False)
        elif fmt == 'json':
            with open(name+'.json', 'w') as json_file:
                json.dump(self.__create(name, description), json_file, indent=2)
        else:
            raise OrcaConfigException('{0} is not a supported workflow format'.format(fmt))
