from typing import Dict, List
from dotted.collection import DottedCollection
from orca.core.config import log


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
