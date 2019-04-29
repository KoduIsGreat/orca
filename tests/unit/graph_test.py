from tests.fixtures.fixtures import config
from orca.core import graph
c = config

def test_graph(c):
    g = graph.loads(c('http_python_csip.yaml'))


def test_graph_multi_roots(c):
    g = graph.loads(c('dot_test.yaml'))
