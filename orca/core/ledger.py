
import uuid
import os
import logging
import pymongo

from orca.core.tasks import OrcaTask
from orca.core.config import OrcaConfig, log
from typing import Dict, List
from datetime import datetime

class Ledger(object):
  """Keeps A record of workflow task executions transactions"""

  # unique for each orca run
  _id = uuid.uuid4()
  
  def set_config(self, config: OrcaConfig):
    self.config = config

  def add(self, task: OrcaTask, state:Dict) -> None:
    """Add an entry to the ledger"""
    print("->> ledger: {0} {1} {2}".format(task.name, str(self._id), str(state)))
    #pass

  def _create_entry(self, task: OrcaTask, state: Dict) -> Dict:
    """Create a dictionary entry to record in a ledger"""
    d = {
          'orca_file': os.path.abspath(self.config.get_yaml_file()), # the workflow file
          'orca_id': self.config.get_version(), # the 'version' entry in the workflow file
          'orca_name': self.config.get_name(), # the 'version' entry in the workflow file (e.g. gitattribute)
          'run_uuid': str(self._id), # the uuid of the current run 
          'run_time': str(datetime.now()), # task execution time
          'task': task.name # the task name
        }
    d.update(state)  # task inputs/outputs
    if log.isEnabledFor(logging.DEBUG):
      log.debug('ledger: {0}'.format(d))
    return d

  def close(self) -> None:
    pass


############################################


class JSONFileLedger(Ledger):
  """Creates a JSON File with a ledger, appends if file exists."""
  
  def __init__(self, file: str):
    self.f = open(file, 'a+')
    log.debug('JSON Ledger: {0}'.format(self.f))

  
  def add(self, task: OrcaTask, state:Dict) -> None:
    d = self._create_entry(task, state)
    self.f.write('{0}\n'.format(d))

    
  def close(self) -> None:
    self.f.close()
    log.debug('closed: {0}'.format(self.f))
    
    
##################################################################    

class MongoLedger(Ledger):
  """Adds entries into a ledger hosted in Mongodb"""
    
  def __init__(self, con: List[str]):
    super().__init__()
    self.mongo = pymongo.MongoClient('mongodb://{0}/'.format(con[0]))
    self.col = self.mongo[con[1]][con[2]]
    log.debug('Mongo Ledger: {0} for {1}'.format(self.mongo, "/".join(con)))

  
  def add(self, task: OrcaTask, state:Dict) -> None:
    d = self._create_entry(task, state)
    self.col.insert_one(d)

    
  def close(self) -> None:
    self.mongo.close()
    log.debug('closed: {0}'.format(self.mongo))
    
