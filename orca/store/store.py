from orca.store import utils
import os
import shutil

from orca.store.workflow import Workflow


class store(object):

    def __repr__(self):
        return 'orca.datastore <%s>' % self.datastore

    def __init__(self, datastore):
        data_path = utils.get_path()
        if not utils.path_exists(data_path):
            os.makedirs(data_path)

        self.datastore = utils.build_path(data_path, datastore)
        if not utils.path_exists(self.datastore):
            os.makedirs(self.datastore.__bytes__())

        self.workflows = self.list_workflows()

    def _create_workflow(self, workflow, overwrite=True):
        workflow_path = utils.build_path(self.datastore, workflow)
        if utils.path_exists(workflow_path):
            if overwrite:
                self.delete_workflow(workflow)
            else:
                raise ValueError("Workflow exists! to Overwrite use overwrite=True")

        os.makedirs(workflow_path.__bytes__())
        os.makedirs(utils.build_path(workflow_path, '_snapshots').__bytes__())

        self.workflows = self.list_workflows()

    def list_workflows(self):
        return utils.subdirs(self.datastore)

    def delete_workflow(self, workflow):
        shutil.rmtree(utils.build_path(self.datastore, workflow))

        self.workflows = self.list_workflows()
        return True

    def workflow(self, workflow, overwrite=True):
        if workflow in self.workflows and not overwrite:
            return Workflow(workflow, self.datastore)

        self._create_workflow(workflow, overwrite)
        return Workflow(workflow, self.datastore)
