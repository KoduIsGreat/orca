import pystore
from pystore.collection import Collection
import os
from dataclasses import dataclass
import logging
from orca.core.config import OrcaConfig
from pandas.io.json import json_normalize
from uuid import uuid4
from orca.core.tasks import OrcaTask

log = logging.getLogger(__name__)


@dataclass
class OrcaCache:
    store: pystore.store
    tasks: Collection

    def get_task(self, task_name: str, snapshot=None, columns=None, filters=None):
        item = self.tasks.item(task_name, snapshot=snapshot, columns=columns, filters=filters)
        log.info('Fetching task {0} data'.format(task_name))
        return OrcaTask(item.metadata, to_json(item.to_pandas()))

    def put_task(self, task: OrcaTask, snapshot: str) -> None:
        log.info('Caching task {0} data.'.format(task.name))
        self.tasks.write(task.name, data=json_normalize(task.locals), metadata=task.task_data, overwrite=True)
        log.info('Cache complete, versioning task data')
        self.tasks.create_snapshot(snapshot)

    def create_snapshot(self):
        snapshot = uuid4()
        self.tasks.create_snapshot(snapshot=snapshot)
        return snapshot


def to_json(df, sep="."):
    def set_for_keys(my_dict, key_arr, val):
        """
        Set val at path in my_dict defined by the string (or serializable object) array key_arr
        """
        current = my_dict
        for i in range(len(key_arr)):
            key = key_arr[i]
            if key not in current:
                if i == len(key_arr) - 1:
                    current[key] = val
                else:
                    current[key] = {}
            else:
                if type(current[key]) is not dict:
                    print("Given dictionary is not compatible with key structure requested")
                    raise ValueError("Dictionary key already occupied")

            current = current[key]

        return my_dict

    result = []
    for _, row in df.iterrows():
        parsed_row = {}
        for idx, val in row.items():
            keys = idx.split(sep)
            parsed_row = set_for_keys(parsed_row, keys, val)

        result.append(parsed_row)
    return result


def connect(config: 'OrcaConfig') -> 'OrcaCache':
    orca_cache_location = os.getenv('ORCA_CACHE_LOCATION', config.get_yaml_dir())
    pystore.set_path(orca_cache_location)
    store = pystore.store('orca')
    log.info('Connecting to cache....')
    collection = store.collection(config.get_name(), overwrite=False)
    log.info('Connected to cache:\nname: {0}\npath: {1}\ncollection: {2}'.format(store.datastore.name,
                                                                                 store.datastore.absolute(),
                                                                                 config.get_name()))
    return OrcaCache(store, tasks=collection)
