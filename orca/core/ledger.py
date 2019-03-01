
from orca.core.tasks import OrcaTask
from orca.core.config import OrcaConfig, log
from typing import Dict, List
from datetime import datetime

import uuid
import os
import logging

class Ledger(object):
  """keeps A record of workflow transactions"""

  # identifies one workflow run
  _id = uuid.uuid4()

  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    print("---> " + task.name + " " + str(self._id) + " " + str(inputs)  + " " + str(outputs))

  def close(self) -> None:
    pass



############################################
  
class LoggingLedger(Ledger):

  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    log.debug("ledger: {0} {1} {3} {4} ".format(task.name, str(self._id), str(inputs), str(outputs)))



############################################
# 
# python3 orca run --json-ledger-file /tmp/f.json for.yaml
#
# maybe import into a db:
# mongoimport --db orca --collection ledger --file /tmp/f.json

class JSONFileLedger(Ledger):
  
  def __init__(self, file: str):
    self.f = open(file, 'a+')
    log.debug('JSON Ledger: {0}'.format(self.f))
  
  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    d = {
           'orca_file': os.path.abspath(config.get_yaml_file()),
           'orca_id': config.get_version(),
           'orca_name': config.get_name(),
           'run_uuid': str(self._id),
           'run_time': str(datetime.now()),
           'task': task.name
        }
    d.update(inputs)
    d.update(outputs)
    
    self.f.write('{0}\n'.format(d))
    if log.isEnabledFor(logging.DEBUG):
      log.debug('{0}'.format(d))
    
  def close(self) -> None:
    self.f.close()
    log.debug('closed: {0}'.format(self.f))
    
