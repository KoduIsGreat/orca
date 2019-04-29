import pytest
from orca.core.validation import validate
from orca.core.errors import ConfigurationError
from tests.fixtures.fixtures import config

config = config


def test_validate(config):
    validate(config('python.yaml'))


def test_validate_complex(config):
    with pytest.raises(ConfigurationError):
        validate(config('uniqueness_task.yaml'))


def test_bad_dependencies(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_bad_task_deps.yaml'))


def test_bad_output_dependencies(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_bad_output_deps.yaml'))


def test_bad_var_dependency(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_bad_var_dep.yaml'))


def test_validate_fork(config):
    validate(config('par.yaml'))


def test_bad_fork_dependency(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_bad_deps_fork.yaml'))


def test_validate_html(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_validate_html.yaml'))


def test_validate_csip(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_valid_csip.yaml'))


def test_valid_bash(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_valid_bash.yaml'))


def test_valid_python(config):
    with pytest.raises(ConfigurationError):
        validate(config('test_valid_python.yaml'))
