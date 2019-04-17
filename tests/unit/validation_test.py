import unittest
import pytest
from tests.util import get_config
from orca.core.validation import validate
from orca.core.errors import ConfigurationError
class ValidationTestCase(unittest.TestCase):

    def test_validate(self):
        config = get_config('python.yaml')
        validate(config)

    def test_validate_complex(self):
        with pytest.raises(ConfigurationError):
            config = get_config('uniqueness_task.yaml')
            validate(config)

    def test_bad_dependencies(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_bad_task_deps.yaml')
            validate(config)

    def test_bad_output_dependencies(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_bad_output_deps.yaml')
            validate(config)

    def test_bad_var_dependency(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_bad_var_dep.yaml')
            validate(config)

    def test_validate_fork(self):
        config = get_config('par.yaml')
        validate(config)

    def test_bad_var_dependency(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_bad_deps_fork.yaml')
            validate(config)

    def test_validate_html(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_validate_html.yaml')
            validate(config)

    def test_validate_csip(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_valid_csip.yaml')
            validate(config)

    def test_valid_bash(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_valid_bash.yaml')
            validate(config)

    def test_valid_python(self):
        with pytest.raises(ConfigurationError):
            config = get_config('test_valid_python.yaml')
            validate(config)
