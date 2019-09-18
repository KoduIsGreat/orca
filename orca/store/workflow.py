from orca.store import utils
import shutil
import time
from orca.store.task import Task
from pandas import DataFrame
import os


class Workflow(object):
    def __repr__(self):
        return "orca.store.workflow <%s>" % self.workflow

    def __init__(self, workflow, datastore):
        self.datastore = datastore
        self.workflow = workflow
        self.tasks = self.list_tasks()
        self.snapshots = self.list_snapshots()

    def _task_path(self, task, as_string=False):
        p = utils.build_path(self.datastore, self.workflow, task)
        if as_string:
            return str(p)
        return p

    def list_tasks(self, **kwargs):
        dirs = utils.subdirs(utils.build_path(self.datastore, self.workflow))
        if not kwargs:
            return dirs

        matched = []
        for d in dirs:
            meta = utils.read_metadata(
                utils.build_path(self.datastore, self.workflow, d)
            )
            del meta["_updated"]

            m = 0
            keys = list(meta.keys())
            for k, v in kwargs.items():
                if k in keys and meta[k] == v:
                    m += 1

            if m == len(kwargs):
                matched.append(d)

        return matched

    def write(self, task, data, meta={}, overwrite=False):
        task_path = self._task_path(task)

        if utils.path_exists(task_path) and not overwrite:
            raise ValueError(
                """
                Task already already exists in workflow, to overwrite set 'overwrite=True'.
            """
            )

        if not utils.path_exists(task_path):
            os.makedirs(self._task_path(task))

        data = data.copy()

        if isinstance(data, DataFrame):
            pass
            # TODO handle dataframe writes

        utils.write_metadata(task_path, metadata=meta)
        utils.write_data(task_path, data)
        self.tasks = self.list_tasks()

    def task(self, task, snapshot=None, filters=None):
        return Task(task, self.datastore, self.workflow, snapshot, filters=filters)

    def delete_task(self, task):
        shutil.rmtree(self._task_path(task))
        self.tasks = self.list_tasks()

    def create_snapshot(self, snapshot=None):
        if snapshot:
            snapshot = "".join(e for e in snapshot if e.isalnum() or e in [".", "_"])
        else:
            snapshot = str(int(time.time() * 1000000))

        src = utils.build_path(self.datastore, self.workflow)
        dst = utils.build_path(src, "_snapshots", snapshot)

        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("_snapshots"))

        self.snapshots = self.list_snapshots()
        return True

    def list_snapshots(self):
        snapshots = utils.subdirs(
            utils.build_path(self.datastore, self.workflow, "_snapshots")
        )
        return snapshots
        # return [s.parts[-1] for s in snapshots]

    def delete_snapshot(self, snapshot):
        if snapshot not in self.snapshots:
            # raise ValueError("Snapshot `%s` doesn't exist" % snapshot)
            return True

        shutil.rmtree(
            utils.build_path(self.datastore, self.workflow, "_snapshots", snapshot)
        )
        self.snapshots = self.list_snapshots()
        return True
