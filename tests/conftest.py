from pytest import fixture, mark
from unconstrained.minizinc import *


SOLVERS = [
    ORTOOLS,
    #CHUFFED,
    #GECODE,
    #COINBC,
]

THREADS = [
    # 0,
    # 2,
    # 4,
    8
]


@fixture(params=SOLVERS)
def minizinc_solver(request) -> Solver:
    return get_solver(request.param)


@fixture(params=THREADS)
def minizinc_threads(request) -> int:
    return request.param


@fixture
def minizinc_options(minizinc_solver, minizinc_threads):
    return MiniZincOptions(
        solver_id = minizinc_solver.id,
        threads = minizinc_threads
    )
