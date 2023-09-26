from pathlib import Path
from unconstrained import minizinc as mz
from pytest import fixture, mark

@fixture
def minizinc_options():
    return mz.SolveOptions()

@fixture
def output_dir():
    return Path('tests/output')