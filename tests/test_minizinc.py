from unconstrained.prelude import *
from unconstrained.minizinc import *
from pytest import mark, fixture
from minizinc.CLI.driver import CLIDriver


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
        constraint a = 1;
        constraint b = true;
        """,
        minizinc_options
        )
    assert result.status == ALL_SOLUTIONS, result.error
    assert result['a']
    assert result['b']


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


@mark.filterwarnings("ignore:model inconsistency")
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


async def test_recursive_predicate_fails(minizinc_options):
    result = await solve(
        """
        predicate recurse(var int: a) =
            recurse(a);
  
        var 1..10: x;
        constraint recurse(x);
        """,
        minizinc_options
        )
    assert result.error
    assert result.status == ERROR



def test_available_solvers():
    solvers = get_available_solvers()
    
    for solver in solvers:
        assert solver


@mark.parametrize('tag', [ORTOOLS, CHUFFED, COINBC, GECODE])
def test_solver_available(tag):
    assert Solver.lookup(tag)
