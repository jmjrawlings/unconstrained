from unconstrained import *
from pytest import mark, fixture


@fixture
def minizinc_solver() -> mz.Solver:
    return mz.get_solver(mz.GECODE)


@fixture
def minizinc_threads() -> int:
    return 8


@fixture
def minizinc_driver() -> mz.Driver:
    return mz.get_driver()


@fixture
def minizinc_options(minizinc_solver, minizinc_threads):
    return mz.SolveOptions(
        solver_id = minizinc_solver.id,
        threads = minizinc_threads
   )


async def test_solve_satisfy(minizinc_options):
    result = await mz.satisfy(
        """
        var bool: b;
        constraint b;
        """,
        minizinc_options,
        name='test satisfy'
        )
    assert result.status == mz.FEASIBLE, result.error
    assert result['b']


async def test_solve_optimise(minizinc_options):
    result = await mz.best_solution(
        """
        var 1..10: a;
        var 1..10: b;
        constraint a < b;
        solve maximize (b - a);
        """,
        minizinc_options,
        name='test optimise'
        )
    assert result.objective == 9, result.error
    assert result.status == mz.OPTIMAL
    assert result['b'] == 10
    assert result['a'] == 1


async def test_syntax_error(minizinc_options):
    result = await mz.best_solution(
        """
        var 1 @#$  %$$%@@@323.10: a;
        var bool: b;
        """,
        minizinc_options,
        name='test syntax'
        )
    assert result.error
    assert result.status == mz.ERROR


async def test_solve_all_solutions(minizinc_options : mz.SolveOptions):
    minizinc_options.solver_id = mz.GECODE
    
    solutions, result = await mz.all_solutions(
        "var {1,2,3}: a;",
        minizinc_options,
        name='test all'
    )
        
    assert result.status == mz.ALL_SOLUTIONS, result.error
    assert {sol['a'] for sol in solutions} == {1,2,3}


@mark.filterwarnings("ignore:model inconsistency")
async def test_solve_unsatisfiable_model(minizinc_options):
    result = await mz.best_solution(
        """
        var 1..1: a;
        var 2..2: b;
        constraint b < a;
        """,
        minizinc_options,
        name='test unsat'
        )
    assert result.status == mz.UNSATISFIABLE


async def test_recursive_predicate_fails(minizinc_options):
    result = await mz.best_solution(
        """
        predicate recurse(var int: a) =
            recurse(a);
  
        var 1..10: x;
        constraint recurse(x);
        """,
        minizinc_options
        )
    assert result.error
    assert result.status == mz.ERROR



def test_get_available_solvers():
    solvers = mz.get_available_solvers()
    
    for solver in solvers:
        assert solver


@mark.parametrize('tag', [mz.ORTOOLS, mz.CHUFFED, mz.COINBC, mz.GECODE])
def test_solver_is_available(tag):
    assert mz.Solver.lookup(tag)
