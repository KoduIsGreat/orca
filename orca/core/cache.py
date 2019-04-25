from dataclasses import dataclass
from typing import Dict

from orca.core.config import OrcaConfig
from orca.core.tasks import OrcaTask
from orca.store.workflow import Workflow
from orca.store import store


def connect(config: OrcaConfig, store_name='orca') -> OrcaConfig:
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

    def store(self, task: OrcaTask):
        self.mem_cache[task.name] = task.locals
        self.workflow_file_cache.write(task.name, task.locals, meta=task.task_data, overwrite=True)
