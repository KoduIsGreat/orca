import unittest
from tests.mocks import tasks
from orca.core.tasks import OrcaTask
from orca.core.handler import ExecutionHandler, ValidationHandler
from orca.core.config import OrcaConfigException
import os


class OrcaHandlerTest(unittest.TestCase):
    pass

    def test_inline_inputs_python(self):
        mock = tasks.inline_python_inputs_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        output = h.handle_python(_task)
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello Adam'

    def test_inline_python(self):
        mock = tasks.inline_python_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        output = h.handle_python(_task)
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello World'

    def test_file_no_inputs_python(self):
        mock = tasks.file_python_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        output = h.handle_python(_task)
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 10

    def test_file_inputs_python(self):
        mock = tasks.file_python_inputs_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        output = h.handle_python(_task)
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 25

    def test_bad_file_python(self):
        mock = tasks.bad_file_path_python
        _task = OrcaTask(mock)
        h = ValidationHandler()
        with self.assertRaises(OrcaConfigException):
            h.handle_python(_task)
