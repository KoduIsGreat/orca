from typing import Dict, List

from orca.core.config import OrcaConfig, resolve_file_path
from orca.core.ledger import Ledger
from orca.core.tasks import OrcaTask
from orca.core.handler import walk
from orca.core.errors import ExecutionError
from orca.core.validation import validate
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import wait
import logging
import re
import requests
import subprocess as subp
from csip import Client
import json
import sys
from orca.core import cache
log = logging.getLogger(__name__)


def __get_call_string(config: Dict, script: str):
    func_name = config.get('callable')
    var_name = config.get('returns', '')
    # match against a function definition string : def <funcname> ( args,...)
    pattern = r'((?P<keyword>def)\s?(?P<function>\w+)\s?\((?P<args>(?P<arg>\w+(,\s?)?)+)?\))'
    # find all functions in the file
    all_funcs = re.findall(pattern, script)
    # take each function string and break it up into a dictionary so we can easily extract the arguments
    dicts = [re.match(pattern, func[0]).groupdict() for func in all_funcs]
    # filter the list of functions for the function the user has defined
    fn_dict = [d for d in dicts if d.get('function') == func_name][0]
    # make the string that will be eval'd
    assignment = var_name if var_name == '' else var_name + ' = '
    args = '' if fn_dict.get('args', '') is None else fn_dict.get('args')
    return '{0}{1}({2})'.format(assignment, func_name, args)


def clean_locals(task: OrcaTask):
    keys_to_remove = [k for k in task.locals if
                      k not in task.outputs and k not in task.inputs]

    for key in keys_to_remove:
        del task.locals[key]


def execute_python(_task: OrcaTask, orca_config: OrcaConfig):
    log.debug("  exec python file : " + _task.python)

    resolved_file = resolve_file_path(orca_config, _task.python, ".py")
    config = _task.config
    try:
        if '.' not in sys.path:
            sys.path.append('.')
        if resolved_file is None:
            exec(_task.python, _task.locals)
        else:
            with open(resolved_file, 'r') as script:
                _task.locals['__file__'] = resolved_file  # if they want to reference __file__ in their script
                _task.locals['__name__'] = script.name  # or the name
                _python = script.read()
                exec(_python, _task.locals)
                if 'callable' in config:
                    call_str = __get_call_string(config, _python)
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
    clean_locals(_task)


def execute_csip(_task: OrcaTask) -> None:
    try:
        client = Client()
        for key, value in _task.locals.items():
            client.add_data(key, value)
        client = client.execute(_task.csip)
        for k, v in client.data.items():
            _task.locals[k] = v['value']
    except requests.exceptions.HTTPError as e:
        raise ExecutionError('An Error occured while making the request:\n {0}'.format(e.response.content))


def execute_http(task: OrcaTask) -> None:
    def handle_method(_task: OrcaTask) -> requests.Response:
        try:
            switch = {
                'GET': lambda _task: requests.get(_task.http, _task.locals, verify=False),
                'PUT': lambda _task, data: requests.put(_task.http, _task.locals, verify=False),
                'POST': lambda _task: requests.post(_task.http, json=_task.locals, verify=False),
                'DELETE': lambda _task: requests.delete(_task.http, verify=False)
            }
            m = _task.config.get('method', 'GET')
            http = switch.get(m)
            return http(_task)
        except KeyError:
            raise ExecutionError(
                'task {0} defines an invalid http method: {1}'.format(_task.name, _task.config.get('method'))
            )

    def handle_response(response: requests.Response) -> Dict:
        try:

            switch = {
                'application/json': lambda r: {'json': json.loads(r.content)},
                'text/html': lambda r: {'html': str(r.content)},
                'text/plain': lambda r: {'text': str(r.content)}
            }
            ct = response.headers.get('content-type').split(';')[0]
            transform_resp = switch.get(ct, lambda r: {'data': r.content})
            return transform_resp(response)
        except KeyError:
            raise ExecutionError('an Invalid content type was defined')

    http_response = handle_method(task)

    if http_response.status_code >= 400:
        task.status = 'failed'
        raise ExecutionError(
            'The http task {0} returned a non ' +
            '200 status\n status code: {1}\n url: {2}'.format(task.name, http_response.status_code, task.http)
        )

    _task_payload = handle_response(http_response)

    for key in _task_payload.keys():
        task.locals[key] = _task_payload[key]

    # remove after execution
    clean_locals(task)


def execute_bash(_task: OrcaTask) -> Dict:
    env = {}
    config = _task.config
    # get defaults
    delimiter = config.get('delimiter', '\n')
    wd = config.get('wd', None)
    if len(_task.locals) > 0:
        env = {key: str(value) for key, value in _task.locals.items()}
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
                print(line)
                o += line + '\n'
        return o
    return {}


def __resolve_task__(task: Dict, config: OrcaConfig, snapshot=None, run_globals={}) -> OrcaTask:
    inputs = task.get('inputs', {})
    _locals = {}
    if inputs:
        inputs = task.get('inputs', {})
        for k, v in inputs.items():
            if str(v).startswith('task.'):
                split = str(v).split('.')
                upstream_task = split[1]
                _locals[k] = config.cache.fetch(upstream_task, filters=split[2:], snapshot=snapshot)
            elif str(v).startswith('var.'):
                split = str(v).split('.')
                defined_var = split[1]
                _locals[k] = eval(str(config.var[defined_var]), globals())  # this should change
            else:
                _locals[k] = eval(str(v), run_globals)

    return OrcaTask(task, _locals)


def __run_task__(task: Dict, config: OrcaConfig, snapshot=None, ledger: Ledger = None,
                 run_globals={}):
    r_task = __resolve_task__(task, config, snapshot=snapshot, run_globals=run_globals)
    if 'python' in task:
        execute_python(r_task, config)
    elif 'bash' in task:
        execute_bash(r_task)
    elif 'http' in task:
        execute_http(r_task)
    elif 'csip' in task:
        execute_csip(r_task)
    if config.cache is not None:
        config.cache.store(r_task)
    if ledger:
        ledger.add(r_task)


def start(config: OrcaConfig, validator=validate, ledger: Ledger = None):
    """
    Closure for executing an orca workflow,
    Validation is performed first then connecting to the pystore cache, then execution
    the `config` and `store` variables are treated as global within the closure scope.
    :param validator: the validator function
    :param config: the orca configuration to execute
    :param ledger: the ledger to write too
    :return:
    """

    def execute_job(job: List[Dict], _config: OrcaConfig, _ledger: Ledger, snapshot=None, start_at=None):
        run_globals = {}  # scoped variables per "job"
        task_queue = walk(job, run_globals=run_globals)
        concurrent_jobs = []
        for task in task_queue:

            if isinstance(task, list):
                concurrent_jobs.append(task)
            elif len(concurrent_jobs) > 0:
                with ThreadPoolExecutor(max_workers=len(concurrent_jobs)) as executor:
                    futures = [executor.submit(execute_job, job, _config, _ledger, snapshot) for job in concurrent_jobs]
                wait(futures)
                concurrent_jobs.clear()
                __run_task__(task, _config, snapshot, _ledger, run_globals)
            else:
                __run_task__(task, _config, snapshot, _ledger, run_globals)

    log.info('checking workflow...')
    validator(config)
    log.info('workflow is valid.')
    log.info('connecting to cache')
    config = cache.connect(config, 'development')
    log.info('successfully connected to cache')
    log.info('starting workflow engine...')
    execute_job(config.job, config, ledger)
    log.info('orca workflow complete!')
