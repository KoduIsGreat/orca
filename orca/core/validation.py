from requests import RequestException
from orca.core.config import OrcaConfig, resolve_file_path
from orca.core.errors import ConfigurationError
from orca.core.handler import walk
from typing import Dict
import requests
import logging
log = logging.getLogger(__name__)


def check_unique(config: OrcaConfig, name: str, task: Dict):
    if name is None or not name.isidentifier():
        raise ConfigurationError('Invalid task name: "{0}"'.format(name))
    task_id = id(task)
    # check against the task dict id to support loops.
    if config.sym_table.get(name, task_id) != task_id:
        raise ConfigurationError("Duplicate task name: {0}".format(name))
    return task_id


def check_task_dependencies(config: OrcaConfig, task: Dict):
    name = task.get('task', None)
    inputs = task.get('inputs', {})
    for k, v in inputs.items():
        if str(v).startswith('task.'):
            split = str(v).split('.')
            upstream_task = split[1]
            defined_dependency = split[2]

            if upstream_task not in config.sym_table:
                raise ConfigurationError('Task {0} defines an upstream task {1} that does not exist.'.format(name, v))

            _utask = config.sym_table.get(upstream_task).get('definition')
            upstream_outputs = _utask.get('outputs', [])
            if defined_dependency not in upstream_outputs:
                raise ConfigurationError(
                    "The input {0} : {1} defined in task {2} is not'" +
                    "defined as an output on task {3}.".format(k, v, name, upstream_task))

        if str(v).startswith('var.'):
            split = str(v).split('.')
            defined_var = split[1]
            if defined_var not in config.var:
                raise ConfigurationError(
                    'The input {0} : {1} defined in task {2} does not exist, check \'var\''.format(k, v, name))


def build_symbol_entry(config: OrcaConfig, task: Dict):
    name = task.get('task', None)
    return name, {
        'id': check_unique(config, name, task),
        'definition': task
    }


def check_variables(config: OrcaConfig):
    log.debug("validating config variable declarations:")
    for key, val in config.var.items():
        if not key.isidentifier():
            raise ConfigurationError(
                'Invalid variable identifier: "{0}"'.format(key))


def check_url(url):
    try:
        r = requests.head(url)
        if r.status_code != 200:
            raise ConfigurationError('The url provided {0} was not accessible.'.format(url))

    except RequestException as e:
        raise ConfigurationError(e.strerror)


def validate_task(config: OrcaConfig, task):
    try:
        name, entry = build_symbol_entry(config, task)
        config.sym_table[name] = entry  # add symbology to table
        check_task_dependencies(config, task)
        if 'bash' in task:
            resolve_file_path(config, task.get('bash'), '.sh')
        elif 'python' in task:
            resolve_file_path(config, task.get('python'), '.py')
        elif 'http' in task:
            check_url(task.get('http'))
        elif 'csip' in task:
            check_url(task.get('csip'))
    except ConfigurationError as e:
        raise e


def validate(config: OrcaConfig):
    check_variables(config)
    for task in walk(job=config.job, visit_all_tasks=True):
        if isinstance(task, list):
            for _t in walk(task, visit_all_tasks=True):
                validate_task(config, _t)
        else:
            validate_task(config, task)
