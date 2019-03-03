import os
import subprocess as subp
import requests

from csip import Client
from typing import List, Dict
from orca.core.tasks import OrcaTask
from orca.core.config import var, task, log, OrcaConfig, OrcaConfigException
from orca.core.ledger import Ledger
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
    log.debug(" handling req result props: {0} -> {1}".format(k, str(v)))
    if k in outputs:
      d[name + "." + k] = v
  return d

def handle_csip_result(response: Dict, outputs: List, name: str) -> Dict:
  d = {}
  for k,v in response.items():
    if k in outputs:
      d[name + "." + k] = v['value']
  return d

def handle_python_result(outputs: List, name: str, task_locals:Dict)-> Dict:
  d = {}
  for out in outputs:
    d[name + '.' + out] = task_locals[out]
  return d



#############################################

class OrcaHandler(metaclass=ABCMeta):
  """ Abstract orca handler for control flow, variable resolution"""
  
  def __init__(self):
    self.symtable = {}
  
  def _check_symtable(self, name:str, task:Dict):
    if name is None or not name.isidentifier():
      raise OrcaConfigException('Invalid task name: "{0}"'.format(name))

    task_id = id(task)
    if self.symtable.get(name, task_id) != task_id:
      raise OrcaConfigException("Duplicate task name: {0}".format(name))
    self.symtable[name] = task_id
      
    
  def handle(self, config: OrcaConfig) -> None:
    self.config = config
    self._handle_sequence(config.job)
    self.close()
  
  def _handle_sequence(self, sequence: Dict) -> None:
    for step in sequence:
      node = next(iter(step))
      if node == "task":
        log.debug(" ---- task: '{}'".format(step['task']))
        self._handle_task(step)
      elif node.startswith("if "):
        log.debug(" ---- if: '{}'".format(node[3:]))
        self._handle_if(step[node], node[3:])
      elif node.startswith("for "):
        log.debug(" ---- for: '{}'".format(node[4:]))
        self._handle_for(step[node], node[4:])
      elif node == "fork":
        log.debug(" ---- fork: ")
        self._handle_fork(step[node])
      elif node.startswith("switch "):
        log.debug(" ---- switch: '{}'".format(node[7:]))
        self._handle_switch(step[node], node[7:])
      else:
        raise OrcaConfigException('Invalid step in job: "{0}"'.format(node))

  def close(self):
    pass
             
  # to be overwritten by subclasses
  @abstractmethod
  def handle_csip(self, task: OrcaTask) -> Dict:
    pass
      
  @abstractmethod  
  def handle_http(self, task: OrcaTask) -> Dict:
    pass
      
  @abstractmethod
  def handle_bash(self, task: OrcaTask) -> Dict:
    pass
    
  @abstractmethod
  def handle_python(self, task: OrcaTask) -> Dict:
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
            
            
  def resolve_task_inputs(self, task_dict: Dict) -> Dict:
    inputs = task_dict.get('inputs',{})
    if inputs:
       return {k: eval(str(v), globals()) for k, v in inputs.items()} 
    return {}


  def _resolve_file_path(self, name: str, ext:str) -> str:
    """ resolve the full qualified path name"""
    try:
      name = eval(str(name), globals())
    except:
      pass
    
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


  def _handle_task(self, task_dict: Dict) -> OrcaTask:
    name = task_dict.get('task', None)
    
    # check the symbol table for task name to be an unique and valid name
    self._check_symtable(name, task_dict)

    # task locals are the resolved inputs, they will be used for 
    # execution
    task_locals = self.resolve_task_inputs(task_dict)
    _task = OrcaTask(task_dict, task_locals)
    
    log.debug(" task '{0}' locals: {1}".format(_task.name, task_locals))
    
    # select the handler and call handle
    handle = self.__select_handler(task_dict)
    result = handle(_task)
    
    log.debug(" task '{0}' locals: {1}".format(_task.name, task_locals))

    # put the tasl_locals into the global task dictonary
    # this includes input and outputs
    task[_task.name] = {}
    for k, v in task_locals.items():
      task[_task.name][k] = v
      
    return _task

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
  
  def __init__(self, ledger: Ledger = None):
    super().__init__()
    self.ledger = ledger or Ledger()
    
  def handle(self, config: OrcaConfig) -> None:
    self.ledger.set_config(config)
    super().handle(config)
  
  def close(self):
    self.ledger.close()


  def _handle_task(self, task_dict: Dict) -> None:
    _task = super()._handle_task(task_dict)
    self.ledger.add(_task, _task.task_locals)

  def handle_csip(self, task: OrcaTask) -> Dict:
    try:
      outputs = task.outputs
      client = Client()
      for key, value in task.inputs.items():
        if isinstance(value, DottedCollection):
          client.add_data(key, value.to_python())
        else:
          client.add_data(key, value)
      client = client.execute(task.csip)
      return handle_csip_result(client.data, outputs, task.name)
    except requests.exceptions.HTTPError as e:
      raise OrcaConfigException(e)
      
      
  def handle_http(self, task: OrcaTask) -> Dict:
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


  def handle_bash(self, task: OrcaTask) -> Dict:
    env = {}
    config = task.config
    # get defaults
    delimiter = config.get('delimiter', '\n')
    wd = config.get('wd', None)
    if len(task.inputs) > 0:
      env = values_tostr(task.inputs)
    sp = subp.Popen(task.bash, env=env, shell=True, stdout=subp.PIPE, stderr=subp.PIPE, cwd=wd)
    out, err = sp.communicate()
    if sp.returncode != 0:
      log.error('return code: {0}'.format(sp.returncode))
    if err:
      for line in err.decode('utf-8').split(delimiter):
          log.error("ERROR: " + line)
    if out:
      o = ""
      for line in out.decode('utf-8').split(delimiter):
        if line:
          o += line + '\n'
      return o
    return {}


  def handle_python(self, _task: OrcaTask) -> Dict:
    log.debug("  exec python file : " + _task.python)
    
    resolved_file = self._resolve_file_path(_task.python, ".py")
    
    if resolved_file is None:
      exec(_task.python, _task.task_locals)
    else:
      with open(resolved_file, 'r') as script:
        exec(script.read(), _task.task_locals)
    
    # remove after execution
    del _task.task_locals['__builtins__']  

    return handle_python_result(_task.outputs, _task.name, _task.task_locals)
      
      
#############################################

class ValidationHandler(OrcaHandler):
  """ValidationHandler, no execution"""

  def __init__(self):
    super().__init__()
  
  def handle_csip(self, task: OrcaTask) -> Dict:
    r = requests.head(task.csip)
    if r.status_code >= 400:
      raise OrcaConfigException('CSIP url not accessible: "{0}"'.format(task.csip))
        
  def handle_http(self, task: OrcaTask) -> Dict:
    r = requests.head(task.http)
    if r.status_code >= 400:
      raise OrcaConfigException('Http url not accessible: "{0}"'.format(task.http))

  def handle_bash(self, task: OrcaTask) -> Dict:
    self._resolve_file_path(task.bash, ".sh")

  def handle_python(self, task: OrcaTask) -> Dict:
    self._resolve_file_path(task.python, ".py")


#############################################

class NoneHandler(OrcaHandler):
  """Handler that does not do anything, useful for testing"""

  def __init__(self):
    super().__init__()
  
  def handle_csip(self, task: OrcaTask)  -> Dict:
    pass
        
  def handle_http(self, task: OrcaTask) -> Dict:
    pass

  def handle_bash(self, task: OrcaTask) -> Dict:
    pass

  def handle_python(self, task: OrcaTask) -> Dict:
    pass


#############################################

class DotfileHandler(OrcaHandler):
  """Handles printing of a dot file"""

  def __init__(self):
    super().__init__()
      
  def handle(self, config: OrcaConfig) -> None:
    self.config = config
    self.dot = ['digraph {',
                'START [shape=doublecircle,color=gray,fontsize=10]',
                'END [shape=doublecircle,color=gray,fontsize=10]',
                'node [style="filled",fontsize=10,fillcolor=aliceblue,color=gray,fixedsize=true]',
                'edge [fontsize=9,fontcolor=dodgerblue3]'
                ]
    self.last_task = 'START'
    self.last_vertex_label = ''
    # first pass: node declaration
    self.decl = True
    # unique id for each node
    self.idx = 0
    self._handle_sequence(config.job)
    self.dot.append('')
    # second pass: vertices 
    self.decl= False
    self.idx = 0
    self._handle_sequence(config.job)
    self.close()
      
      
  def _handle_fork(self, sequences:Dict) -> None:
    """Handle parallel execution"""
    name = "fork_{0}".format(self.idx) 
    term = "term_{0}".format(self.idx) 
    self.idx += 1
    if self.decl:
      self.dot.append('{0} [shape=house,fillcolor=cornsilk,fontcolor="dodgerblue3",label="FORK"]'.format(name))
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
    name = "for_{0}".format(self.idx) 
    term = "term_{0}".format(self.idx) 
    self.idx += 1
    if self.decl:
      self.dot.append('{0} [shape=trapezium,fillcolor=cornsilk,fontcolor="dodgerblue3",label="FOR\\n{1}"]'.format(name, var_expr))
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
    name = "switch_{0}".format(self.idx) 
    term = "term_{0}".format(self.idx) 
    self.idx += 1
    if self.decl:
      self.dot.append('{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="SWITCH\\n{1}"]'.format(name,cond))
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
    name = "if_{0}".format(self.idx) 
    term = "term_{0}".format(self.idx) 
    self.idx += 1
    if self.decl:
      self.dot.append('{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="IF\\n{1}"]'.format(name, cond))
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
            

  def close(self):
    self.dot.append("{0} -> END".format(self.last_task))
    self.dot.append("}")
    path, ext = os.path.splitext(self.config.get_yaml_file())
    with open(path + ".dot", "w") as text_file:
      print("\n".join(self.dot), file=text_file)
    log.info("generated dot file '" + path + ".dot'")
        
        
  def _ht(self, name: str, shape: str, label:str = '' ):
    if self.decl:
      self.dot.append('{0} [shape={1}, label="\'{0}\'\\n{2}"]'.format(name, shape, label))
    else:
      self.dot.append('{0} -> {1} {2}'.format(self.last_task, name , self.last_vertex_label))
      self.last_vertex_label = ''
      self.last_task = name
        
  def handle_csip(self, task: OrcaTask):
    self._ht(task.name, 'cds', task.csip)
        
        
  def handle_http(self, task: OrcaTask):
    self._ht(task.name, 'cds', task.http)


  def handle_bash(self, task: OrcaTask):
    self._ht(task.name, 'note')


  def handle_python(self, task: OrcaTask):
    self._ht(task.name, 'note', task.python)
  
