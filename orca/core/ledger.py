
from orca.core.tasks import OrcaTask
from orca.core.config import OrcaConfig, log
from typing import Dict, List

import uuid

class Ledger(object):
  """keeps A record of workflow transactions"""

  # identifies one workflow run
  _id = uuid.uuid4()

  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    print("---> " + task.name + " " + str(self._id) + " " + str(inputs)  + " " + str(outputs))

  def close(self) -> None:
    pass
  

############################################

class JSONFileLedger(Ledger):
  
  def __init__(self, file: str):
    self.f = open(file, 'a+')
    log.debug('JSON Ledger: {0}'.format(self.f))
  
  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    d = {
           'orca_name': config.get_name(),
           'orca_id': config.get_name(),
           'run_id': self._id,
           'task': task.name
        }
    d.update(inputs)
    d.update(outputs)
    
    self.f.write('{0}\n'.format(d))
    log.debug('{0}'.format(d))
    
  def close(self) -> None:
    self.f.close()
    log.debug('closed: {0}'.format(self.f))
    
