from abc import ABCMeta, abstractmethod
from orca.core.tasks import OrcaTask


class Ledger(metaclass=ABCMeta):
  """keeps A record of workflow transactions"""

  @abstractmethod  
  def add(task: OrcaTask) -> None:
    pass

  @abstractmethod  
  def close() -> None:
    pass



############################################

class JSONFileLedger(Ledger):
  
  # Transaction cd ...id, identifies a workflow execution
  tuuid = ""
  
  def __init__(self, file: str):
    self.csv = open(file, 'w')
  
  def add(task: OrcaTask) -> None:
    self.csv.write('{0},'.format(task.name)
    
  def close() -> None:
    self.csv.close()
    
