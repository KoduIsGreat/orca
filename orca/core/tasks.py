import logging
from typing import Dict, List
from csip import Client
from dotted.collection import DottedCollection
import requests
import subprocess
log = logging.getLogger(__name__)


class OrcaTaskException(Exception):
    pass


class OrcaTask(object):

    def __init__(self, task_dict: Dict):
        self.task_data = task_dict

    @property
    def name(self) -> str:
        try:
            return self.task_data.get('task')
        except KeyError as e:
            raise OrcaTaskException("Missing Task Identifier: ", e)

    @property
    def inputs(self) -> Dict:
        return self.task_data.get('inputs', {})

    @property
    def outputs(self) -> List:
        return self.task_data.get('outputs', [])

    @property
    def config(self) -> Dict:
        try:
            return self.task_data.get('config', {})
        except KeyError as e:
            raise OrcaTaskException("Missing required config: ", e)

    @property
    def csip(self) -> str:
        return self.task_data.get('csip')

    @property
    def http(self) -> str:
        return self.task_data.get('http')

    @property
    def bash(self) -> str:
        return self.task_data.get('bash')

    @property
    def python(self) -> str:
        return self.task_data.get('python')


def resolve(value: object) -> object:
    """resolve the value against the globals"""
    return eval(str(value))


def resolve_dict(d: Dict) -> Dict:
    resolved = {key: resolve(value) for key, value in d.items()}
    return resolved


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


def handle_csip(task: OrcaTask) -> Dict:
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
        return handle_service_result(client.data, outputs, name)
    except requests.exceptions.HTTPError as e:
        raise OrcaTaskException(e)


def handle_http(task: OrcaTask) -> Dict:
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


def handle_bash( task: OrcaTask):
    env = {}
    cmd = task.bash
    config = task.config
    # get defaults
    delimiter = config.get('delimiter', '\n')
    errmsg = config.get('errmsg', "unspecified error")
    exit_on_err = config.get("exitOnError", True)
    wd = config.get('wd', None)

    if len(task.inputs) > 0:
        env = values_tostr(task.inputs)
    sp = subprocess.Popen(cmd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=wd)
    out, err = sp.communicate()
    if err:
        for line in err.split('\n'):
            print("ERROR: " + line)
    if sp.returncode != 0 and exit_on_err is True:
        print('ERROR: ' + str(sp.returncode) + " " + errmsg)
    if out:
        o = ""
        for line in out.decode('utf-8').split(delimiter):
            if line:
                o += line + '\n'
        return o
    return {}


def handle_python(task: OrcaTask):
    print("  exec python file : " + task.python)
    exec(open(task.python).read(), globals())
    return {}

