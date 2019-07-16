import unittest
import pytest
from orca.core.errors import ExecutionError
from orca.core import engine
from tests.fixtures.fixtures import config

config = config

def test_dates_example(config):
    engine.start(config('imports.yaml'))


def test_http_json(config):
    engine.start(config('http_json.yaml'))


def test_http_task(config):
    engine.start(config('http.yaml'))


def test_simple_python(config):
    engine.start(config('python.yaml'))


def test_python_globals(config):
    engine.start(config('python_globals.yaml'))


def test_inline_bash_task(config):
    engine.start(config('bash-inline.yaml'))


def test_csip_task(config):
    engine.start(config('csip.yaml'))


def test_fork_task(config):
    engine.start(config('par.yaml'))


def test_for_task(config):
    engine.start(config('for.yaml'))


def test_for_vars(config):
    engine.start(config('for_with_variable.yaml'))


def test_fork(config):
    engine.start(config('test_fork.yaml'))


def test_switch_task(config):
    engine.start(config('switch.yaml'))


# def test_http_python_csip(config):
#     engine.start(config('http_python_csip.yaml'))


def test_var1_task(config):
    engine.start(config('var1.yaml'))


def test_var2_task(config):
    engine.start(config('var2.yaml'))


def test_var3_task(config):
    engine.start(config('var3.yaml'))


def test_var4_task(config):
    engine.start(config('var4.yaml'))


def test_python_func(config):
    engine.start(config('python_funcs.yaml'))


def test_bad_python_func(config):
    with pytest.raises(ExecutionError):
        engine.start(config('bad_python_func.yaml'))


def test_cache(config):
    engine.start(config('cache_tests.yaml'))


if __name__ == '__main__':
    unittest.main()
