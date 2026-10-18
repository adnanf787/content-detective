import pandas as pd
import pytest
from src.loader import Manifest
from src.analysis import prepare


@pytest.fixture
def build():
    def make(rows, **metadata):
        manifest = Manifest(**metadata)
        frame, quality = prepare(pd.DataFrame(rows), manifest)
        return frame, quality, manifest
    return make
