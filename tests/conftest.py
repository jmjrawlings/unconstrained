from unconstrained import *
from pytest import fixture, mark

@fixture
def minizinc_options():
    return MiniZincOptions()

@fixture
def output_dir():
    return Path('tests/output')