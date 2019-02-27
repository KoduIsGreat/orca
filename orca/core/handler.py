import os
import sys
import requests
import subprocess

from csip import Client
from typing import List, Dict, TextIO
from orca.core.tasks import OrcaTask
from orca.core.config import var,task
from concurrent.futures import ThreadPoolExecutor
from dotted.collection import DottedCollection
from abc import ABCMeta, abstractmethod

## some global utility functions

def values_tostr(d: Dict) -> Dict:
    a = {key: str(value) for key, value in d.items()}
    return a

def handle_service_result(response: Dict, outputs, name: str) -> Dict:
    d = dict()
    for k, v in response.items():
        print(" handling req result props: {0} -> {1}".format(k, str(v)))
        if k in outputs:
            d[name + "." + k] = v
    return d

def handle_csip_result(response: Dict, outputs: List, name: str) -> Dict:
    d = dict()
    for k,v in response.items():
        if k in outputs:
            d[name + "." + k] = v['value']
    return d

def handle_python_result(outputs: List, name: str)-> Dict:
    d = dict()
    for v in outputs:
        d[name + '.' + v] = eval(v, globals())
    return d




####

class OrcaHandler(metaclass=ABCMeta):
    """ Base orca handler class for control flow, variable resolution"""
  
    def handle(self, config: 'OrcaConfig') -> None:
        self.config = config
        self.__handle_sequence(config.job)
  
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
             
             
    # to be overwritten by subclasses
    @abstractmethod
    def handle_csip(self, task: OrcaTask, yaml_dir: str) -> Dict:
        pass
      
    @abstractmethod  
    def handle_http(self, task: OrcaTask, yaml_dir: str) -> Dict:
        pass
      
    @abstractmethod
    def handle_bash(self, task: OrcaTask, yaml_dir: str) -> Dict:
        pass
    
    @abstractmethod
    def handle_python(self, task: OrcaTask, yaml_dir: str) -> Dict:
        pass

    def __select_handler(self, task_dict: Dict):
        if 'csip' in task_dict:
            return self.handle_csip
        elif 'http' in task_dict:
            return self.handle_http
        elif 'bash' in task_dict:
            return self.handle_bash
        elif 'python' in task_dict:
            return self.handle_python
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
        result = handle(_task, self.config.get_yaml_dir())
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
        with ThreadPoolExecutor(max_workers=(len(sequences))) as executor:
            for sequence in sequences:
                executor.submit(self.__handle_sequence, sequence)





####

class ExecutionHandler(OrcaHandler):
    """Execution Handler, executes csip, bash, python, http"""

    def handle_csip(self, task: OrcaTask, yaml_dir: str) -> Dict:
        try:
            url = task.csip
            name = task.name
            outputs = task.outputs
            client = Client()
            for key, value in task.inputs.items():
                if isinstance(value, DottedCollection):
                    client.add_data(key, value.to_python())
                else:
                    client.add_data(key, value)
            client = client.execute(url)
            return handle_csip_result(client.data, outputs, name)
        except requests.exceptions.HTTPError as e:
            raise OrcaTaskException(e)
          
          
    def handle_http(self, task: OrcaTask, yaml_dir: str) -> Dict:
        url = task.http
        name = task.name
        inputs = task.inputs
        if 'method' not in task.config:
            raise OrcaTaskException("requests service operator must include method: service {0}".format(name))
        if task.config['method'] == 'GET':
            return handle_service_result(requests.get(url, params=task.config['params']).content, name)
        elif task.config['method'] == 'POST':
            if isinstance(inputs, DottedCollection):
                return handle_service_result(requests.post(url, inputs.to_python()).content, name)
            else:
                return handle_service_result(requests.post(url, inputs).content, name)


    def handle_bash(self, task: OrcaTask, yaml_dir: str):
        env = {}
        cmd = task.bash
        config = task.config
        # get defaults
        delimiter = config.get('delimiter', '\n')
        wd = config.get('wd', None)
        if len(task.inputs) > 0:
            env = values_tostr(task.inputs)
        sp = subprocess.Popen(cmd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=wd)
        out, err = sp.communicate()
        if sp.returncode != 0:
            print('code: ' + str(sp.returncode))
        if err:
            for line in err.decode('utf-8').split(delimiter):
                print("ERROR: " + line)
        if out:
            o = ""
            for line in out.decode('utf-8').split(delimiter):
                if line:
                    o += line + '\n'
            return o
        return {}

    def handle_python(self, task: OrcaTask, yaml_dir: str):
        print("  exec python file : " + task.python)
        for k, v in task.inputs.items():
            if isinstance(v, str):
                v = "\'{0}\'".format(v)
            fmt = '{0} = {1}'.format(k, v)
            exec(fmt, locals(), globals())

        if os.path.isabs(task.python) and os.path.isfile(task.python):
            # absolute path provided
            exec(open(task.python).read(), globals())
        else:
            if not os.path.isabs(task.python) and os.path.isfile(os.path.join(yaml_dir, task.python)):
                # path relative to yaml file
                exec(open(os.path.join(yaml_dir, task.python)).read(), globals())
            else: 
                # python inlined
                exec(task.python, globals())

        return handle_python_result(task.outputs, task.name)


