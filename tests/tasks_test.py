import unittest
from orca.core.tasks import handle_python
from tests.mocks.tasks import inline_python_mock, inline_python_inputs_mock, file_python_inputs_mock, file_python_mock
from orca.core.tasks import OrcaTask
import os


class OrcaHandlerTest(unittest.TestCase):

    def test_inline_inputs_python(self):
        mock = inline_python_inputs_mock
        _task = OrcaTask(mock)
        output = handle_python(_task,  os.getcwd())
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello Adam'

    def test_inline_python(self):
        mock = inline_python_mock
        _task = OrcaTask(mock)
        output = handle_python(_task, os.getcwd())
        assert _task.name+'.greeting' in output
        assert output[_task.name+'.greeting'] == 'Hello World'

    def test_file_no_inputs_python(self):
        mock = file_python_mock
        _task = OrcaTask(mock)
        output = handle_python(_task, os.getcwd())
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 10

    def test_file_inputs_python(self):
        mock = file_python_inputs_mock
        _task = OrcaTask(mock)
        output = handle_python(_task, os.getcwd())
        assert _task.name+'.result' in output
        assert output[_task.name+'.result'] == 25
