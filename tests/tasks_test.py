import unittest
from tests.mocks.tasks import inline_python_mock, inline_python_inputs_mock, file_python_inputs_mock, file_python_mock
from orca.core.tasks import OrcaTask
from orca.core.handler import ExecutionHandler
import os


class OrcaHandlerTest(unittest.TestCase):
    pass

    def test_inline_inputs_python(self):
        mock = inline_python_inputs_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        output = h.handle_python(_task)
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello Adam'

    def test_inline_python(self):
        mock = inline_python_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        output = h.handle_python(_task)
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello World'

    def test_file_no_inputs_python(self):
        mock = file_python_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        output = h.handle_python(_task)
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 10

    def test_file_inputs_python(self):
        mock = file_python_inputs_mock
        _task = OrcaTask(mock)
        h = ExecutionHandler()
        output = h.handle_python(_task)
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 25
