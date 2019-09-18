import unittest
from tests.mocks import tasks
from orca.core.tasks import OrcaTask
from orca.core.handler import ExecutionHandler, ValidationHandler
from orca.core.errors import ConfigurationError
from tests.util import get_config
from orca.core.handler import walk


class OrcaHandlerTest(unittest.TestCase):
    def test_walk_job(self):
        config = get_config("python_funcs.yaml")
        for task in walk(config.job):
            assert task is not None

    def test_walk_job_if_visit_children(self):
        config = get_config("visit_if.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=True):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 3

    def test_walk_job_if_visit_children_false(self):
        config = get_config("visit_if.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=False):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 2

    def test_walk_job_nested_if(self):
        config = get_config("visit_if_nested.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=True):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 4

    def test_walk_job_nested_if(self):
        config = get_config("visit_if_nested.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=False):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 2

    def test_walk_job_for(self):
        config = get_config("for_with_variable.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=True):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 2

    def test_walk_job_switch(self):
        config = get_config("switch.yaml")
        count = 0
        for task in walk(config.job, visit_all_tasks=True):
            count += 1
            assert task is not None
            assert "task" in task
        assert count == 6

    def test_walk_job_fork(self):
        config = get_config("par.yaml")
        count = 0
        for task_list in walk(config.job, visit_all_tasks=False):
            count += len(task_list) if isinstance(task_list, list) else 1
        assert count == 5

    def test_inline_inputs_python(self):
        mock = tasks.inline_python_inputs_mock
        # _task = OrcaTask(mock, mock)
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert "greeting" in _task.locals
        assert _task.locals["greeting"] == "Hello Adam"

    def test_inline_python(self):
        mock = tasks.inline_python_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert "greeting" in _task.locals
        assert _task.locals["greeting"] == "Hello World"

    def test_file_no_inputs_python(self):
        mock = tasks.file_python_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert "result" in _task.locals
        assert _task.locals["result"] == 10

    def test_file_inputs_python(self):
        mock = tasks.file_python_inputs_mock
        h = ExecutionHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        h.handle_python(_task)
        assert "result" in _task.locals
        assert _task.locals["result"] == 25

    def test_bad_file_python(self):
        mock = tasks.bad_file_path_python
        h = ValidationHandler()
        _task = OrcaTask(mock, h.resolve_task_inputs(mock))
        with self.assertRaises(ConfigurationError):
            h.handle_python(_task)
