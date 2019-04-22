# from typing import Dict
#
# import pystore
# from pystore.collection import Collection
# import os
# from dataclasses import dataclass
# import logging
# from orca.core.config import OrcaConfig
# from pandas.io.json import json_normalize
# from uuid import uuid4
# from orca.core.tasks import OrcaTask
# from pathlib import Path
# import shutil
# log = logging.getLogger(__name__)
#
# from os.path import expanduser as _expanduser
# DFEAULT_ORCA_PATH = _expanduser('~/orca')
#
# def get_path( *args):
#     return Path(os.path.join(os.getenv('ORCA_CACHE_LOCATION', DFEAULT_ORCA_PATH), *args))
#
# def build_path(*args):
#     return Path(os.path.join(*args))
#
# def set_path(path):
#     if path is None:
#         path = get_path()
#
#     else:
#         path = path.rstrip('/').rstrip('\\').rstrip(' ')
#         if "://" in path and "file://" not in path:
#             raise ValueError("OrcaStorage only works with local file system")
#     path = get_path()
#     if not path_exists(path):
#         os.makedirs(get_path().__bytes__())
#
#     return get_path()
#
# def path_exists(path: Path):
#     return path.exists()
#
# def subdirs(d):
#     """ use this to construct paths for future storage support """
#     return [o.parts[-1] for o in Path(d).iterdir()
#             if o.is_dir() and o.parts[-1] != '_snapshots']
#
# def list_workflows():
#     if not path_exists(get_path()):
#         os.makedirs(get_path().__bytes__())
#     return subdirs(get_path())
#
# def delete_workflows():
#     shutil.rmtree(get_path())
#     return True
#
# def delete_workflow(workflow):
#     shutil.rmtree(get_path(workflow))
#     return True
#
#
#
# class OrcaWorkflow(object):
#
# class OrcaStore(object):
#
#     def __repr__(self):
#         return 'orca.datastore <%s>' % self.datastore
#
#     def __init__(self, datastore):
#         data_path = get_path()
#         if not path_exists(data_path):
#             os.makedirs(data_path)
#
#         self.datastore = build_path(data_path, datastore)
#         if not path_exists(self.datastore):
#             os.makedirs(self.datastore.__bytes__())
#
#         self.workflows = list_workflows()
#
#
#     def _create_workflow(self, workflow, overwrite=True):
#         workflow_path = build_path(self.datastore, workflow)
#         if path_exists(workflow_path):
#             if overwrite:
#                 delete_workflow(workflow)
#             else:
#                 raise ValueError("Workflow exists! to Overwrite use overwrite=True")
#
#         os.makedirs(workflow_path.__bytes__())
#         os.makedirs(build_path(workflow_path, '_snapshots').__bytes__())
#
#         self.workflows = list_workflows()
#
# # @dataclass
# # class OrcaCache:
# #     store: pystore.store
# #     tasks: Collection
# #
# #     def get_task(self, task_name: str, snapshot=None, columns=None, filters=None):
# #         item = self.tasks.item(task_name, snapshot=snapshot, columns=columns, filters=filters)
# #         log.info('Fetching task {0} data'.format(task_name))
# #         return to_json(item.data)[0]
# #
# #     def put_task(self, task: OrcaTask) -> None:
# #         log.info('Caching task {0} data.'.format(task.name))
# #         self.tasks.write(task.name, data=json_normalize(task.locals), metadata=task.task_data, overwrite=True)
# #         log.info('Cache complete, versioning task data')
# #         # self.tasks.create_snapshot(snapshot)
# #
# #     def create_snapshot(self):
# #         snapshot = uuid4()
# #         self.tasks.create_snapshot(snapshot=snapshot)
# #         return snapshot
#
#
# def connect(config: 'OrcaConfig') -> 'OrcaCache':
#     orca_cache_location = os.getenv('ORCA_CACHE_LOCATION', config.get_yaml_dir())
#     pystore.set_path(orca_cache_location)
#     store = pystore.store('orca')
#     log.info('Connecting to cache....')
#     collection = store.collection(config.get_name(), overwrite=False)
#     log.info('Connected to cache:\nname: {0}\npath: {1}\ncollection: {2}'.format(store.datastore.name,
#                                                                                  store.datastore.absolute(),
#                                                                                  config.get_name()))
#     return OrcaCache(store, tasks=collection)
