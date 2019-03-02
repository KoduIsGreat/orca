
import uuid
import os
import logging
import pymongo

from orca.core.tasks import OrcaTask
from orca.core.config import OrcaConfig, OrcaConfigException, log
from typing import Dict, List
from datetime import datetime

class Ledger(object):
  """Keeps A record of workflow task executions transactions"""

  # unique for each orca run
  _id = uuid.uuid4()

  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    """Add an entry to the ledger"""
    print("->> ledger: {0} {1} {2} {3} ".format(task.name, str(self._id), str(inputs), str(outputs)))
    pass

  def _create_entry(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> Dict:
    """Create a dictionary entry to record in a ledger"""
    d = {
          'orca_file': os.path.abspath(config.get_yaml_file()), # the workflow file
          'orca_id': config.get_version(), # the 'version' entry in the workflow file
          'orca_name': config.get_name(), # the 'version' entry in the workflow file (e.g. gitattribute)
          'run_uuid': str(self._id), # the uuid of the current run 
          'run_time': str(datetime.now()), # task execution time
          'task': task.name # the task name
        }
    d.update(inputs)  # task inputs/outputs
    d.update(outputs)
    if log.isEnabledFor(logging.DEBUG):
      log.debug('ledger: {0}'.format(d))
    return d

  def close(self) -> None:
    pass


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
    d = self._create_entry(config, task, inputs, outputs)
    self.f.write('{0}\n'.format(d))

    
  def close(self) -> None:
    self.f.close()
    log.debug('closed: {0}'.format(self.f))
    
    
##################################################################    
# python3 orca run --json-ledger-file /tmp/f.json for.yaml

class MongoLedger(Ledger):
    
  def __init__(self, connect_str: str):
    mc = connect_str.split('/')
    self.c = pymongo.MongoClient('mongodb://{0}/'.format(mc[0]))
    db = self.c[mc[1]]
    self.col = db[mc[2]]
    log.debug('Mongo Ledger: {0} for {1}'.format(self.c, connect_str))

  
  def add(self, config: OrcaConfig, task: OrcaTask, inputs:Dict, outputs:Dict) -> None:
    d = self._create_entry(config, task, inputs, outputs)
    self.col.insert_one(d)

    
  def close(self) -> None:
    self.c.close()
    log.debug('closed: {0}'.format(self.c))
    
    
