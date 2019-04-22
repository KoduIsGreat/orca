from orca.store import utils
from pandas.io.json import json_normalize


class Task(object):

    def __repr__(self):
        return "orca.store.task <%s,%s>" % (self.workflow, self.task)

    def __init__(self, task, datastore, workflow, snapshot, filters=None):
        self.datastore = datastore
        self.workflow = workflow
        self.snapshot = snapshot
        self.task = task

        self._path = utils.build_path(datastore, workflow, task)

        if snapshot:
            snap_path = utils.build_path(datastore, workflow, '_snapshots', snapshot)

            self._path = utils.build_path(snapshot, task)

            if not utils.path_exists(snap_path):
                raise ValueError("Snapshot %s doesn't exist" % snapshot)
            else:
                if not utils.path_exists(self._path):
                    raise ValueError("Item %s doesn't exist in this snapshot" % task)

        self.metadata = utils.read_metadata(self._path)
        self.data = utils.read_data(self._path, filters=filters)

    def to_pandas(self, metadata_path, records_path):
        return json_normalize(self.data, record_path=records_path, meta=metadata_path)
