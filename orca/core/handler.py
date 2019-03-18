import os
import subprocess as subp
import requests
import json
import re
from csip import Client
from typing import List, Dict
from orca.core.tasks import OrcaTask
from orca.core.config import task, log, OrcaConfig
from orca.core.ledger import Ledger
from concurrent.futures import ThreadPoolExecutor
from dotted.collection import DottedCollection
from abc import ABCMeta, abstractmethod
from orca.core.errors import ConfigurationError, ExecutionError
from orca.core.config import var  # noqa: F401


# some global utility functions


def values_tostr(d: Dict) -> Dict:
    return {key: str(value) for key, value in d.items()}


def handle_service_result(response: Dict, outputs, name: str) -> Dict:
    d = {}
    for k, v in response.items():
        log.debug(" handling req result props: {0} -> {1}".format(k, str(v)))
        if k in outputs:
            d[name + "." + k] = v
    return d


def handle_csip_result(response: Dict, outputs: List, name: str) -> Dict:
    d = {}
    for k, v in response.items():
        if k in outputs:
            try:
                d[name + "." + k] = v['value']
            except KeyError as e:
                raise ExecutionError(
                    "Output variable {0} not found, message: {1}," +
                    "\n the response from the task was: {2}".format(k, e, json.dumps(response, indent=2)))
    return d


def handle_python_result(outputs: List, name: str, task_locals: Dict) -> Dict:
    d = {}
    for out in outputs:
        try:
            d[name + '.' + out] = task_locals[out]
        except KeyError as e:
            raise ExecutionError("Task output not found: {0}".format(out), e)
    return d


#############################################

class OrcaHandler(metaclass=ABCMeta):
    """ Abstract orca handler for control flow, variable resolution"""

    def __init__(self):
        self.symtable = {}

    def _check_symtable(self, name: str, task: Dict):
        if name is None or not name.isidentifier():
            raise ConfigurationError('Invalid task name: "{0}"'.format(name))
        task_id = id(task)
        # check against the task dict id to support loops.
        if self.symtable.get(name, task_id) != task_id:
            raise ConfigurationError("Duplicate task name: {0}".format(name))
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
            elif node == "if":
                log.debug(" ---- if: '{}'".format(step['if']))
                self._handle_if(step)
            elif node == "for":
                log.debug(" ---- for: '{}'".format(step['for']))
                self._handle_for(step)
            elif node.startswith("fork"):
                log.debug(" ---- fork: ")
                self._handle_fork(step['fork'])
            elif node == "switch":
                log.debug(" ---- switch: '{}'".format(step['switch']))
                self._handle_switch(step)
            else:
                raise ConfigurationError(
                    'Invalid step in job: "{0}"'.format(node))

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
            raise ConfigurationError(
                'Invalid task type: "{0}"'.format(task_dict))

    def resolve_task_inputs(self, task_dict: Dict) -> Dict:
        inputs = task_dict.get('inputs', {})
        if inputs:
            return {k: eval(str(v), globals()) for k, v in inputs.items()}
        return {}

    def _resolve_file_path(self, name: str, ext: str) -> str:
        """ resolve the full qualified path name"""

        # potential value resolution if this should be a file name
        try:
            name = eval(str(name), globals())
        except Exception as e:
            # ok, never mind
            log.debug(e)

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
                    # this should be a file but it's not.
                    raise ConfigurationError(
                        'File not found: "{0}"'.format(name))
                return None

    def _handle_task(self, task_dict: Dict) -> OrcaTask:
        name = task_dict.get('task', None)

        # check the symbol table for task name to be an unique and valid name
        self._check_symtable(name, task_dict)

        # task_locals are the resolved inputs, they will be used for
        # execution
        task_locals = self.resolve_task_inputs(task_dict)
        _task = OrcaTask(task_dict, task_locals)

        log.debug("task '{0}' locals pre: {1}".format(_task.name, task_locals))

        # select the handler and call handle
        handle = self.__select_handler(task_dict)
        log.info('Starting task {0}'.format(name))
        result = handle(_task)
        log.info('Task {0} completed'.format(name, ))

        log.debug("task '{0}' locals post: {1}".format(
            _task.name, task_locals))

        # put the task_locals into the global task dictonary
        # this includes input and outputs
        task[_task.name] = {}
        for k, v in task_locals.items():
            task[_task.name][k] = v

        return _task

    # control structures
    def _handle_if(self, condition_block: Dict) -> None:
        """Handle 'if'"""
        cond = condition_block['if']
        sequence = condition_block['do']
        if eval(cond, globals()):
            self._handle_sequence(sequence)

    def _handle_switch(self, condition_block: Dict) -> None:
        """Handle 'switch'"""
        cond = condition_block['switch']
        case = eval(cond, globals())
        seq = condition_block.get(case, condition_block.get('default', None))
        if seq is not None:
            self._handle_sequence(seq)

    def _handle_for(self, condition_block: Dict) -> None:
        """Handle 'for'"""
        var_expr = condition_block['for']
        i = var_expr.find(",")
        if i == -1:
            raise ConfigurationError(
                'Invalid "for" expression: "{0}"'.format(var_expr))

        var = var_expr[:i]
        if not var.isidentifier():
            raise ConfigurationError(
                'Not a valid identifier: "{0}"'.format(var))

        expr = var_expr[i + 1:]
        for i in eval(expr, globals()):
            # mapping loop variable 'i' to 'var'
            q = ''
            if isinstance(i, str):
                q = "'"
            exec("{0}={2}{1}{2}".format(var, i, q), globals())
            self._handle_sequence(condition_block['do'])

    def _handle_fork(self, sequences: Dict) -> None:
        """Handle 'fork'"""
        with ThreadPoolExecutor(max_workers=(len(sequences))) as executor:
            for sequence in sequences:
                executor.submit(self._handle_sequence, sequence)


#############################################

class ExecutionHandler(OrcaHandler):
    """Execution Handler, executes csip, bash, python, http"""

    def __init__(self, ledger: Ledger = None):
        super().__init__()
        self.ledger = ledger or Ledger()
        self.validator = ValidationHandler()

    def handle(self, config: OrcaConfig) -> None:
        log.info('Executing workflow...')
        self.ledger.set_config(config)
        super().handle(config)

    def close(self) -> None:
        self.ledger.close()

    def _handle_task(self, task_dict: Dict) -> None:
        _task = super()._handle_task(task_dict)
        self.ledger.add(_task)

    def handle_csip(self, _task: OrcaTask) -> Dict:
        try:
            client = Client()
            for key, value in _task.locals.items():
                if isinstance(value, DottedCollection):
                    client.add_data(key, value.to_python())
                else:
                    client.add_data(key, value)
            client = client.execute(_task.csip)
            return handle_csip_result(client.data, _task.outputs, _task.name)
        except requests.exceptions.HTTPError as e:
            raise ExecutionError(e)

    def handle_http(self, _task: OrcaTask) -> Dict:
        url = _task.http
        name = _task.name
        inputs = _task.locals
        headers = _task.config.get('header')
        content_type = headers.get('content-type', 'text/plain')

        if 'method' not in _task.config:
            raise ConfigurationError(
                "requests service operator must include method: service {0}".format(name))

        if _task.config.get('method') == 'GET':
            return handle_service_result(json.loads(requests.get(url, params=_task.config.get('params', None)).content),
                                         _task.outputs, name)
        elif _task.config['method'] == 'POST':
            if isinstance(inputs, DottedCollection):
                return handle_service_result(json.loads(requests.post(url, inputs.to_python()).content), _task.outputs,
                                             name)
            else:
                return handle_service_result(json.loads(requests.post(url, inputs).content), _task.outputs, name)

    def handle_bash(self, _task: OrcaTask) -> Dict:
        env = {}
        config = _task.config
        # get defaults
        delimiter = config.get('delimiter', '\n')
        wd = config.get('wd', None)
        if len(_task.locals) > 0:
            env = values_tostr(_task.locals)
        sp = subp.Popen(_task.bash, env=env, shell=True,
                        stdout=subp.PIPE, stderr=subp.PIPE, cwd=wd)
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

    def __get_call_string(self, config: Dict, script: str):
        func_name = config.get('callable')
        var_name = config.get('returns', '')
        # match against a function definition string : def <funcname> ( args,...)
        pattern = r'((?P<keyword>def)\s?(?P<function>\w+)\s?\((?P<args>(?P<arg>\w+(,\s?)?)+)\))'
        # find all functions in the file
        all_funcs = re.findall(pattern, script)
        # take each function string and break it up into a dictionary so we can easily extract the arguments
        dicts = [re.match(pattern, func[0]).groupdict() for func in all_funcs]
        # filter the list of functions for the function the user has defined
        fn_dict = [d for d in dicts if d.get('function') == func_name][0]
        # make the string that will be eval'd
        assignment = var_name if var_name == '' else var_name + ' = '
        return '{0}{1}({2})'.format(assignment, func_name, fn_dict.get('args', ''))

    def handle_python(self, _task: OrcaTask):
        log.debug("  exec python file : " + _task.python)

        resolved_file = self._resolve_file_path(_task.python, ".py")
        config = _task.config
        try:
            if resolved_file is None:
                exec(_task.python, _task.locals)
            else:
                with open(resolved_file, 'r') as script:
                    _python = script.read()
                    exec(_python, _task.locals)
                    if 'callable' in config:
                        call_str = self.__get_call_string(config, _python)
                        exec(call_str, _task.locals)

            _task.status = "success"
        except IndexError:
            raise ExecutionError(
                'The function {0} was not defined in the file: {1}'.format(_task.config.get('callable'), _task.python)
            )
        except BaseException as e:
            _task.status = "failed"
            log.debug(str(e))
            raise
        # remove after execution
        keys_to_remove = [k for k in _task.locals if
                          k not in _task.outputs and k not in _task.inputs]

        for key in keys_to_remove:
            del _task.locals[key]


#############################################

class ValidationHandler(OrcaHandler):
    """ValidationHandler, no execution"""

    def __init__(self):
        super().__init__()

    def handle_csip(self, _task: OrcaTask):
        r = requests.head(_task.csip)
        if r.status_code >= 400:
            raise ConfigurationError(
                'Task {0} defines a CSIP endpoint that is not accessible: "{1}"'.format(_task.name, _task.csip)
            )

    def handle_http(self, _task: OrcaTask):
        r = requests.head(_task.http)
        if r.status_code >= 400:
            raise ConfigurationError(
                'Task {0} defines a Http url that is not accessible: "{1}"'.format(_task.name, _task.http)
            )

    def handle_bash(self, _task: OrcaTask):
        try:
            self._resolve_file_path(_task.bash, ".sh")
        except ConfigurationError as e:
            raise ConfigurationError(
                'Task {0} defines a bash script that cannot be found: {1}'.format(_task.name, _task.bash), e
            )

    def handle_python(self, _task: OrcaTask):
        try:
            self._resolve_file_path(_task.python, ".py")
        except ConfigurationError as e:
            raise ConfigurationError(
                'Task {0} defines a python script that cannot be found: {1}'.format(_task.name, _task.python), e
            )


#############################################

class NoneHandler(OrcaHandler):
    """Handler that does not do anything, useful for testing"""

    def __init__(self):
        super().__init__()

    def handle_csip(self, task: OrcaTask) -> Dict:
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
        self.decl = False
        self.idx = 0
        self._handle_sequence(config.job)
        self.close()

    def _handle_fork(self, sequences: Dict) -> None:
        """Handle parallel execution"""
        name = "fork_{0}".format(self.idx)
        term = "term_{0}".format(self.idx)
        self.idx += 1
        if self.decl:
            self.dot.append(
                '{0} [shape=house,fillcolor=cornsilk,fontcolor="dodgerblue3",label="FORK"]'.format(name))
            self.dot.append('{0} [shape=point]'.format(term))
            for sequence in sequences:
                self._handle_sequence(sequence)
        else:
            self.dot.append(
                '{0} -> {1} {2}'.format(self.last_task, name, self.last_vertex_label))
            self.last_vertex_label = ''
            for sequence in sequences:
                self.last_task = name
                self._handle_sequence(sequence)
                self.dot.append('{0} -> {1}'.format(self.last_task, term))
            self.last_task = term

    def _handle_for(self, conditional_block: Dict, ) -> None:
        """Handle Looping"""
        var_expr = conditional_block['for']
        sequence = conditional_block['do']
        name = "for_{0}".format(self.idx)
        term = "term_{0}".format(self.idx)
        self.idx += 1
        if self.decl:
            self.dot.append(
                '{0} [shape=trapezium,fillcolor=cornsilk,fontcolor="dodgerblue3",label="FOR\\n{1}"]'.format(name,
                                                                                                            var_expr))
            self.dot.append('{0} [shape=point]'.format(term))
            self._handle_sequence(sequence)
        else:
            self.dot.append(
                '{0} -> {1} {2}'.format(self.last_task, name, self.last_vertex_label))
            self.last_vertex_label = ''
            self.last_task = name
            self._handle_sequence(sequence)
            self.dot.append('{0} -> {1}'.format(self.last_task, term))
            self.dot.append('{0} -> {1} [style="dotted"]'.format(term, name))
            self.last_task = term

    def _handle_switch(self, conditional_block: Dict, ) -> None:
        """Handle conditional switch."""
        cond = conditional_block['switch']
        cases = conditional_block.copy()
        cases.pop('switch')
        name = "switch_{0}".format(self.idx)
        term = "term_{0}".format(self.idx)
        self.idx += 1
        if self.decl:
            self.dot.append(
                '{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="SWITCH\\n{1}"]'.format(name,
                                                                                                             cond))
            self.dot.append('{0} [shape=point]'.format(term))
            for case, seq in cases.items():
                self._handle_sequence(seq)
        else:
            self.dot.append(
                '{0} -> {1} {2}'.format(self.last_task, name, self.last_vertex_label))
            self.last_vertex_label = ''
            for case, seq in cases.items():
                self.last_task = name
                self.last_vertex_label = '[label="{0}"]'.format(case)
                self._handle_sequence(seq)
                self.dot.append('{0} -> {1}'.format(self.last_task, term))
            self.last_task = term

    def _handle_if(self, conditional_block: Dict) -> None:
        """Handle if."""
        cond = conditional_block['if']
        sequence = conditional_block['do']
        name = "if_{0}".format(self.idx)
        term = "term_{0}".format(self.idx)
        self.idx += 1
        if self.decl:
            self.dot.append(
                '{0} [shape=diamond,fillcolor=cornsilk,fontcolor="dodgerblue3",label="IF\\n{1}"]'.format(name, cond))
            self.dot.append('{0} [shape=point]'.format(term))
            self._handle_sequence(sequence)
        else:
            self.dot.append(
                '{0} -> {1} {2}'.format(self.last_task, name, self.last_vertex_label))
            self.last_task = name
            self.last_vertex_label = '[label="true"]'
            self._handle_sequence(sequence)
            self.dot.append('{0} -> {1}'.format(self.last_task, term))
            self.dot.append('{0} -> {1} [label="false"]'.format(name, term))
            self.last_task = term

    def close(self):
        self.dot.append("{0} -> END".format(self.last_task))
        self.dot.append("}")
        path, ext = os.path.splitext(self.config.get_yaml_file())
        with open(path + ".dot", "w") as text_file:
            print("\n".join(self.dot), file=text_file)
        log.info("generated dot file '" + path + ".dot'")

    def _ht(self, name: str, shape: str, label: str = ''):
        if self.decl:
            self.dot.append(
                '{0} [shape={1}, label="\'{0}\'\\n{2}"]'.format(name, shape, label))
        else:
            self.dot.append(
                '{0} -> {1} {2}'.format(self.last_task, name, self.last_vertex_label))
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
