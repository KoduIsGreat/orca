from orca.core.cache import connect
from tests.fixtures.fixtures import config

config = config


def test_connect(config):
    c = connect(config('cache_tests.yaml'))
    assert c.cache is not None
