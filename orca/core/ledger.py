import uuid
import os
import logging
import pymongo
import json

from orca.core.tasks import OrcaTask
from orca.core.config import OrcaConfig, log
from typing import Dict, List
from datetime import datetime
from pykafka import KafkaClient


class Ledger(object):
    """Keeps A record of workflow task executions transactions"""

    def __init__(self):
        # unique for each orca run
        self._id = uuid.uuid4()

    def set_config(self, config: OrcaConfig) -> None:
        self.config = config

    def add(self, task: OrcaTask) -> None:
        """Add an entry to the ledger"""
        # print("->> ledger: {0}".format(self._create_entry(task)))
        pass

    def _create_entry(self, task: OrcaTask) -> Dict:
        """Create a dictionary entry to record in a ledger"""
        d = {
            # the workflow file
            'orca_file': os.path.abspath(self.config.get_yaml_file()),
            # the 'version' entry in the workflow file
            'orca_id': self.config.get_version(),
            # the 'version' entry in the workflow file (e.g. gitattribute)
            'orca_name': self.config.get_name(),
            'task_name': task.name,  # the task name
            'task_uuid': str(self._id),  # the uuid of the current run
            'task_status': task.status,  # status of the run
            'task_time': str(datetime.now()),  # task execution time
            'task_data': task.locals,  # task data
        }
        if log.isEnabledFor(logging.DEBUG):
            log.debug('ledger: {0}'.format(d))
        return d

    def close(self) -> None:
        pass


############################################


class JSONFileLedger(Ledger):
    """Creates a JSON File with a ledger, appends if file exists."""

    def __init__(self, file: str):
        super().__init__()
        self.f = open(file, 'a+')
        log.debug('JSON Ledger: {0}'.format(self.f))

    def add(self, task: OrcaTask) -> None:
        self.f.write('{0}\n'.format(json.dumps(self._create_entry(task))))

    def close(self) -> None:
        self.f.close()
        log.debug('closed: {0}'.format(self.f))


############################################

class MongoLedger(Ledger):
    """Adds entries into a ledger hosted in Mongodb"""

    def __init__(self, con: List[str]):
        super().__init__()
        self.mongo = pymongo.MongoClient('mongodb://{0}/'.format(con[0]))
        self.col = self.mongo[con[1]][con[2]]
        log.debug('Mongo Ledger: {0} for {1}'.format(
            self.mongo, "/".join(con)))

    def add(self, task: OrcaTask) -> None:
        self.col.insert_one(self._create_entry(task))

    def close(self) -> None:
        self.mongo.close()
        log.debug('closed: {0}'.format(self.mongo))


#############################################


class KafkaLedger(Ledger):
    """ Kafka ledger"""

    def __init__(self, con: List[str]):
        super().__init__()
        self.kafka = KafkaClient(hosts=con[0])
        topic = self.kafka.topics[con[1]]
        self.producer = topic.get_producer()

    def add(self, task: OrcaTask) -> None:
        self.producer.produce(json.dumps(self._create_entry(task)))

    def close(self) -> None:
        self.kafka.close()
        log.debug('closed: {0}'.format(self.kafka))
