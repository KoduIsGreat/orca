from abc import ABCMeta, abstractmethod
from orca.core.tasks import OrcaTask


class Transaction(metaclass=ABCMeta):
  """keeps A record of workflow transactions"""

  @abstractmethod  
  def record(task: OrcaTask) -> None:
    pass

  @abstractmethod  
  def close() -> None:
    pass


############################################

class CSVTracer(Transaction):
  
  # Transaction cd ...id, identifies a workflow execution
  tuuid = ""
  
  def __init__(self, file: str):
    self.csv = open(file, 'w')
  
  def record(task: OrcaTask) -> None:
    self.csv.write('{0},'.format(task.name)
    
  def close() -> None:
    self.csv.close()
    
