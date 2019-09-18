import os
import pytest
from orca.core.config import OrcaConfig

fixture_path = os.path.dirname(__file__)


@pytest.fixture
def config():
    def _loader(file_name) -> OrcaConfig:
        path = os.path.join(fixture_path, "configs", file_name)
        with open(path, "r") as p:
            return OrcaConfig.create(p)

    return _loader
