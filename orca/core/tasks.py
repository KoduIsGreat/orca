from typing import Dict, List
from orca.core.errors import ConfigurationError


# TODO clean this up.
# TODO use hash _id to check to see if task should be ran again.
# TODO create a "State" task map indcating the completion status of tasks, will be needed for implicit parallelization


class OrcaTask(object):
    def __init__(self, task_dict: Dict, task_locals: Dict):
        self.task_data = task_dict
        self.id = id(task_dict)
        self._status = "unknown"
        self._task_locals = task_locals

    @property
    def name(self) -> str:
        try:
            return self.task_data.get("task")
        except KeyError as e:
            raise ConfigurationError("Missing Task Identifier: ", e)

    @property
    def locals(self) -> Dict:
        """The resolved inputs and generated ouputs"""
        return self._task_locals

    @property
    def inputs(self) -> Dict:
        """The inputs as found in the yaml file"""
        return self.task_data.get("inputs", {})

    @property
    def outputs(self) -> List:
        """The outputs as found in the yaml file"""
        return self.task_data.get("outputs", [])

    @property
    def config(self) -> Dict:
        return self.task_data.get("config", {})

    @property
    def csip(self) -> str:
        return self.task_data.get("csip")

    @property
    def http(self) -> str:
        return self.task_data.get("http")

    @property
    def bash(self) -> str:
        return self.task_data.get("bash")

    @property
    def python(self) -> str:
        return self.task_data.get("python")

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, st: str):
        self._status = st
