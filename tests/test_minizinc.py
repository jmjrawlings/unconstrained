from unconstrained import *
from pytest import mark, fixture


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


async def test_solve_simple_satisfy_model(minizinc_options):
    result = await best_minizinc_solution(
        """
        var 1..10: a;
        var bool: b;
        """,
        minizinc_options
        )
    assert result.status == SolveStatus.FEASIBLE


async def test_solve_simple_optimise_model(minizinc_options):
    result = await best_minizinc_solution(
        """
        var 1..10: a;
        var 1..10: b;
        constraint a < b;
        solve maximize (b - a);
        """,
        minizinc_options
        )
    assert result.objective == 9
    assert result.status == SolveStatus.OPTIMAL
    assert result['b'] == 10
    assert result['a'] == 1