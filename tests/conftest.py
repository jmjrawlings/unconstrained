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
def solver(request) -> Solver:
    return get_solver(request.param)



@fixture(params=THREADS)
def threads(request) -> int:
    return request.param


@fixture
def minizinc_options(solver, threads):
    return MiniZincOptions(
        solver_id = solver.id,
        threads = threads
    )