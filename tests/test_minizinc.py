from curses import ERR
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
    return SolveOptions(
        solver_id = minizinc_solver.id,
        threads = minizinc_threads
    )


async def test_solve_satisfy(minizinc_options):
    result = await best_solution(
        """
        var 1..10: a;
        var bool: b;
        """,
        minizinc_options
        )
    assert result.status == FEASIBLE


async def test_solve_optimise(minizinc_options):
    result = await best_solution(
        """
        var 1..10: a;
        var 1..10: b;
        constraint a < b;
        solve maximize (b - a);
        """,
        minizinc_options
        )
    assert result.objective == 9
    assert result.status == OPTIMAL
    assert result['b'] == 10
    assert result['a'] == 1


async def test_syntax_error(minizinc_options):
    result = await best_solution(
        """
        var 1 @#$  %$$%@@@323.10: a;
        var bool: b;
        """,
        minizinc_options
        )
    assert result.error
    assert result.status == ERROR