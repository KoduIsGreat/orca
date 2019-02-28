import os
import sys
import requests
import subprocess
import requests

from csip import Client
from typing import List, Dict, TextIO
from orca.core.tasks import OrcaTask
from orca.core.config import var,task,OrcaConfig
from concurrent.futures import ThreadPoolExecutor
from dotted.collection import DottedCollection
from abc import ABCMeta, abstractmethod

## some global utility functions

def values_tostr(d: Dict) -> Dict:
    a = {key: str(value) for key, value in d.items()}
    return a

def handle_service_result(response: Dict, outputs, name: str) -> Dict:
    d = {}
    for k, v in response.items():
        print(" handling req result props: {0} -> {1}".format(k, str(v)))
        if k in outputs:
            d[name + "." + k] = v
    return d

def handle_csip_result(response: Dict, outputs: List, name: str) -> Dict:
    d = {}
    for k,v in response.items():
        if k in outputs:
            d[name + "." + k] = v['value']
    return d

def handle_python_result(outputs: List, name: str)-> Dict:
    d = {}
    for v in outputs:
        d[name + '.' + v] = eval(v, globals())
    return d



#############################################

class OrcaHandler(metaclass=ABCMeta):
    """ Abstract orca handler for control flow, variable resolution"""
    
    def handle(self, config: OrcaConfig) -> None:
        self.config = config
        self._handle_sequence(config.job)
  
    def _handle_sequence(self, sequence: Dict) -> None:
        for step in sequence:
            node = next(iter(step))
            if node == "task":
                print(" ---- task: '{}'".format(step['task']))
                self.__handle_task(step)
            elif node.startswith("if "):
                print(" ---- if: '{}'".format(node[3:]))
                self._handle_if(step[node], node[3:])
            elif node.startswith("for "):
                print(" ---- for: '{}'".format(node[4:]))
                self._handle_for(step[node], node[4:])
            elif node == "fork":
                print(" ---- fork: ")
                self._handle_fork(step[node])
            elif node.startswith("switch "):
                print(" ---- switch: '{}'".format(node[7:]))
                self._handle_switch(step[node], node[7:])
            else:
                raise OrcaConfigException('Invalid step in job: "{0}"'.format(node))
             
             
    # to be overwritten by subclasses
    @abstractmethod
    def handle_csip(self, task: OrcaTask) -> None:
        pass
      
    @abstractmethod  
    def handle_http(self, task: OrcaTask) -> None:
        pass
      
    @abstractmethod
    def handle_bash(self, task: OrcaTask) -> None:
        pass
    
    @abstractmethod
    def handle_python(self, task: OrcaTask) -> None:
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
      
    def _resolve_file_path(self, name: str, ext:str) -> str:
        """ resolve the full qualified path name"""
        if os.path.isfile(name):
            return name
        else:
            # maybe change this, because of testing
            if hasattr(self, 'config'):
                yaml_dir = self.config.get_yaml_dir()
            else:
                yaml_dir = "."
            rel_path = os.path.join(yaml_dir, name)
            if os.path.isfile(rel_path):
                # path relative to yaml file
                return rel_path
            else:
                if name.endswith(ext):
                    raise OrcaConfigException('File not found: "{0}"'.format(name))
                return None

    def __handle_task(self, task_dict: Dict) -> None:
        name = task_dict.get('task', None)
        if name is None or not name.isidentifier():
            raise OrcaConfigException('Invalid task name: "{0}"'.format(name))
        handle = self.__select_handler(task_dict)
        resolved_task = self.__resolve_task(task_dict.copy())
        _task = OrcaTask(resolved_task)
        result = handle(_task)
        if isinstance(result, dict):
            for k, v in result.items():
                task[k] = v
        elif isinstance(result, str):
            print(result)

    # control structures
    def _handle_if(self, sequence:Dict, cond:str) -> None:
        """Handle if."""
        if eval(cond, globals()):
            self._handle_sequence(sequence)
            
    def _handle_switch(self, sequence:Dict, cond:str) -> None:
        """Handle conditional switch."""
        c = eval(cond, globals())
        seq = sequence.get(c, sequence.get("default", None))
        if seq is not None:
            self._handle_sequence(seq)
 
    def _handle_for(self, sequence:Dict, var_expr:str) -> None:
        """Handle Looping"""
        i = var_expr.find(",")
        if i == -1:
            raise OrcaConfigException('Invalid "for" expression: "{0}"'.format(var_expr))
        var = var_expr[:i]
        if not var.isidentifier():
            raise OrcaConfigException('Not a valid identifier: "{0}"'.format(var))
        expr = var_expr[i+1:]
        for i in eval(expr, globals()):
            exec("{0}='{1}'".format(var,i), globals())
            self._handle_sequence(sequence)

    def _handle_fork(self, sequences:Dict) -> None:
        """Handle parallel execution"""
        with ThreadPoolExecutor(max_workers=(len(sequences))) as executor:
            for sequence in sequences:
                executor.submit(self._handle_sequence, sequence)




#############################################

class ExecutionHandler(OrcaHandler):
    """Execution Handler, executes csip, bash, python, http"""

    def handle_csip(self, task: OrcaTask) -> None:
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
          
          
    def handle_http(self, task: OrcaTask) -> None:
        url = task.http
        name = task.name
        inputs = task.inputs
        if 'method' not in task.config:
            raise OrcaConfigException("requests service operator must include method: service {0}".format(name))
        if task.config['method'] == 'GET':
            return handle_service_result(requests.get(url, params=task.config['params']).content, name)
        elif task.config['method'] == 'POST':
            if isinstance(inputs, DottedCollection):
                return handle_service_result(requests.post(url, inputs.to_python()).content, name)
            else:
                return handle_service_result(requests.post(url, inputs).content, name)


    def handle_bash(self, task: OrcaTask) -> None:
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
            print('return code: ' + str(sp.returncode))
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


    def handle_python(self, task: OrcaTask) -> None:
        print("  exec python file : " + task.python)
        for k, v in task.inputs.items():
            if isinstance(v, str):
                v = "\'{0}\'".format(v)
            fmt = '{0} = {1}'.format(k, v)
            exec(fmt, locals(), globals())
        
        resolved_file = self._resolve_file_path(task.python, ".py")
        if resolved_file is None:
            exec(task.python, globals())
        else: 
            exec(open(resolved_file).read(), globals())

        return handle_python_result(task.outputs, task.name)
      
      
#############################################

class ValidationHandler(OrcaHandler):
    """ValidationHandler, no execution"""
    
    def handle_csip(self, task: OrcaTask):
        r = requests.head(task.csip)
        if r.status_code >= 400:
            raise OrcaConfigException('CSIP url not accessible: "{0}"'.format(task.csip))
          
    def handle_http(self, task: OrcaTask):
        r = requests.head(task.http)
        if r.status_code >= 400:
            raise OrcaConfigException('Http url not accessible: "{0}"'.format(task.http))

    def handle_bash(self, task: OrcaTask):
        self._resolve_file_path(task.bash, ".sh")

    def handle_python(self, task: OrcaTask):
        self._resolve_file_path(task.python, ".py")


#############################################

class NoneHandler(OrcaHandler):
    """Handler that does not do anything, useful for testing"""
    
    def handle_csip(self, task: OrcaTask):
        pass
          
    def handle_http(self, task: OrcaTask):
        pass

    def handle_bash(self, task: OrcaTask):
        pass

    def handle_python(self, task: OrcaTask):
        pass


#############################################

class DotfileHandler(OrcaHandler):
    """Handles printing of a dot file"""
      
    def handle(self, config: OrcaConfig) -> None:
        self.config = config
        self.start()
        self.decl = True
        self.idx = 0
        self._handle_sequence(config.job)
        self.dot.append('')
        self.decl= False
        self.idx = 0
        self._handle_sequence(config.job)
        self.end()
        
    def _handle_fork(self, sequences:Dict) -> None:
        """Handle parallel execution"""
        name = "fork_" + str(self.idx) 
        term = "term_" + str(self.idx) 
        self.idx += 1
        if self.decl:
            self.dot.append('{0} [shape=house,fillcolor=cornsilk,fontcolor="dodgerblue3",label="fork"]'.format(name))
            self.dot.append('{0} [shape=point]'.format(term))
            for sequence in sequences:
                self._handle_sequence(sequence)
        else:
            self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
            self.last_vertex_label = ''
            for sequence in sequences:
                self.last_task = name
                self._handle_sequence(sequence)
                self.dot.append('{0} -> {1}'.format(self.last_task,term))
            self.last_task = term
        
    def _handle_for(self, sequence:Dict, var_expr:str) -> None:
        """Handle Looping"""
        name = "for_" + str(self.idx) 
        term = "term_" + str(self.idx) 
        self.idx += 1
        if self.decl:
            self.dot.append('{0} [shape=trapezium,fillcolor=cornsilk,fontcolor="dodgerblue3",label="for",xlabel="{1}"]'.format(name, var_expr))
            self.dot.append('{0} [shape=point]'.format(term))
            self._handle_sequence(sequence)
        else:
            self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
            self.last_vertex_label = ''
            self.last_task = name
            self._handle_sequence(sequence)
            self.dot.append('{0} -> {1}'.format(self.last_task,term))
            self.dot.append('{0} -> {1} [style="dotted"]'.format(term,name))
            self.last_task = term

    def _handle_switch(self, sequence:Dict, cond:str) -> None:
        """Handle conditional switch."""
        name = "switch_" + str(self.idx) 
        term = "term_" + str(self.idx) 
        self.idx += 1
        if self.decl:
            self.dot.append('{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="switch",xlabel="{1}"]'.format(name,cond))
            self.dot.append('{0} [shape=point]'.format(term))
            for case, seq in sequence.items():
                self._handle_sequence(seq)
        else:
            self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
            self.last_vertex_label = ''
            for case, seq in sequence.items():
                self.last_task = name
                self.last_vertex_label = '[label="{0}"]'.format(case)
                self._handle_sequence(seq)
                self.dot.append(self.last_task + ' -> ' + term )
            self.last_task = term

    def _handle_if(self, sequence:Dict, cond:str) -> None:
        """Handle if."""
        name = "if_" + str(self.idx) 
        term = "term_" + str(self.idx) 
        self.idx += 1
        if self.decl:
            self.dot.append('{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="if",xlabel="{1}"]'.format(name, cond))
            self.dot.append('{0} [shape=point]'.format(term))
            self._handle_sequence(sequence)
        else:
            self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
            self.last_task = name
            self.last_vertex_label = '[label="true"]'
            self._handle_sequence(sequence)
            self.dot.append('{0} -> {1}'.format(self.last_task,term))
            self.dot.append('{0} -> {1} [label="false"]'.format(name, term))
            self.last_task = term
            
    def start(self):
        self.dot = ['digraph {',
                  'start [shape=doublecircle,color=gray,fontsize=10]',
                  'end [shape=doublecircle,color=gray,fontsize=10]',
                  'node [style="filled",fontsize=10,fillcolor=aliceblue]',
                  'edge [fontsize=9,fontcolor=dodgerblue3]'
                  ]
        self.last_task = 'start'
        self.last_vertex_label = ''
      
    def end(self):
        self.dot.append("{0} -> end".format(self.last_task))
        self.dot.append("}")
        path, ext = os.path.splitext(self.config.get_yaml_file())
        with open(path + ".dot", "w") as text_file:
            print("\n".join(self.dot), file=text_file)
        print("generated dot file '" + path + ".dot'")
        
    def _ht(self, name, shape):
        if self.decl:
          self.dot.append('{0} [shape={1}]'.format(name, shape))
        else:
          self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
          self.last_vertex_label = ''
          self.last_task = name
        
    def handle_csip(self, task: OrcaTask):
        self._ht(task.name, 'cds')
          
    def handle_http(self, task: OrcaTask):
        self._ht(task.name, 'cds')

    def handle_bash(self, task: OrcaTask):
        self._ht(task.name, 'note')

    def handle_python(self, task: OrcaTask):
        self._ht(task.name, 'note')
  
