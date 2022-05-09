from src import *
from pytest import fixture, mark

@fixture
def minizinc_options():
    return SolveOptions()

@fixture
def output_dir():
    return Path('tests/output')