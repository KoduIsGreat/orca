from dataclasses import dataclass
from typing import Dict

from orca.core.config import OrcaConfig, task
from orca.core.tasks import OrcaTask
from orca.store.workflow import Workflow
from orca.store import store


# TODO hook this parameterization of store_name into commands as an option, or set as an env var
# TODO update filter to use multiple filters, currently will overwrite
# TODO refactor to no longer depend on dotted "task" global var, included now for backwards compatibility with examples

def connect(config: OrcaConfig, store_name='development') -> OrcaConfig:
    s = store(store_name)
    w = s.workflow(config.name)
    config.cache = OrcaCache(w, {})
    return config


@dataclass
class OrcaCache:
    workflow_file_cache: Workflow
    mem_cache: Dict

    def fetch(self, task_name, filters=(), snapshot=None):
        if task_name not in self.mem_cache:
            self.mem_cache[task_name] = self.workflow_file_cache.task(task_name, snapshot=snapshot).data
        if filters:
            tmp = self.mem_cache[task_name]
            for f in filters:
                tmp = tmp.get(f, None)
                if tmp is None:
                    raise ValueError("""
                        Property %s was not found 
                    """ % f)
            return tmp
        return self.mem_cache[task_name]

    def store(self, _task: OrcaTask):
        task[_task.name] = _task.locals
        self.mem_cache[_task.name] = _task.locals
        self.workflow_file_cache.write(_task.name, _task.locals, meta=_task.task_data, overwrite=True)
