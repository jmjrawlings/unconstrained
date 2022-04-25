from curses import ERR
from unconstrained import *
from pytest import mark, fixture
from minizinc.CLI.driver import CLIDriver
from minizinc import find_driver


@fixture
def minizinc_solver() -> Solver:
    return get_solver(ORTOOLS)


@fixture
def minizinc_threads() -> int:
    return 8

@fixture
def minizinc_driver() -> CLIDriver:
    return find_driver()


@fixture
def minizinc_options(minizinc_solver, minizinc_threads):
    return SolveOptions(
        solver_id = minizinc_solver.id,
        threads = minizinc_threads
    )


async def test_solve_satisfy(minizinc_options):
    result = await solve(
        """
        var 1..10: a;
        var bool: b;
        """,
        minizinc_options
        )
    assert result.status == FEASIBLE


async def test_solve_optimise(minizinc_options):
    result = await solve(
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
    result = await solve(
        """
        var 1 @#$  %$$%@@@323.10: a;
        var bool: b;
        """,
        minizinc_options
        )
    assert result.error
    assert result.status == ERROR


async def test_solve_unsatisfiable(minizinc_options):
    result = await solve(
        """
        var 1..1: a;
        var 2..2: b;
        constraint b < a;
        """,
        minizinc_options
        )
    assert result.status == UNSATISFIABLE


def test_available_solvers():
    solvers = get_available_solvers()
    
    for solver in solvers:
        assert solver


@mark.parametrize('tag', [ORTOOLS, CHUFFED, COINBC, GECODE])
def test_solver_available(tag):
    assert Solver.lookup(tag)
