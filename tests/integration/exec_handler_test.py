import unittest
import pytest
from orca.core.errors import ExecutionError
from orca.core import engine
from tests.fixtures.fixtures import config

config = config

def test_imports_example(config):
    engine.execute(config('imports.yaml'))


def test_http_json(config):
    engine.execute(config('http_json.yaml'))


def test_http_task(config):
    engine.execute(config('http.yaml'))


def test_simple_python(config):
    engine.execute(config('python.yaml'))


def test_python_globals(config):
    engine.execute(config('python_globals.yaml'))


def test_inline_bash_task(config):
    engine.execute(config('bash-inline.yaml'))


def test_csip_task(config):
    engine.execute(config('csip.yaml'))


def test_fork_task(config):
    engine.execute(config('par.yaml'))


def test_for_task(config):
    engine.execute(config('for.yaml'))


def test_switch_task(config):
    engine.execute(config('switch.yaml'))


# def test_http_python_csip(config):
#     run_handler('http_python_csip.yaml', ExecutionHandler())


def test_var1_task(config):
    engine.execute(config('var1.yaml'))


def test_var2_task(config):
    engine.execute(config('var2.yaml'))


def test_var3_task(config):
    engine.execute(config('var3.yaml'))


def test_var4_task(config):
    engine.execute(config('var4.yaml'))


def test_python_func(config):
    engine.execute(config('python_funcs.yaml'))


def test_bad_python_func(config):
    with pytest.raises(ExecutionError):
        engine.execute(config('bad_python_func.yaml'))


if __name__ == '__main__':
    unittest.main()
