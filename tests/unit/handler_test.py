import unittest
from tests.mocks import tasks
from orca.core.tasks import OrcaTask
from orca.core.handler import ExecutionHandler, ValidationHandler
from orca.core.errors import ConfigurationError


class OrcaHandlerTest(unittest.TestCase):

    def test_inline_inputs_python(self):
        mock = tasks.inline_python_inputs_mock
        # _task = OrcaTask(mock, mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert 'greeting' in _task.locals
        assert _task.locals['greeting'] == 'Hello Adam'

    def test_inline_python(self):
        mock = tasks.inline_python_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert 'greeting' in _task.locals
        assert _task.locals['greeting'] == 'Hello World'

    def test_file_no_inputs_python(self):
        mock = tasks.file_python_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert 'result' in _task.locals
        assert _task.locals['result'] == 10

    def test_file_inputs_python(self):
        mock = tasks.file_python_inputs_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert 'result' in _task.locals
        assert _task.locals['result'] == 25

    def test_bad_file_python(self):
        mock = tasks.bad_file_path_python
        h = ValidationHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        with self.assertRaises(ConfigurationError):
            h.handle_python(_task)
