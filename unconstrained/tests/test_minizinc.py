from unconstrained import *
from pytest import mark, fixture


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


@mark.skip(reason='Find a better way to do this')
async def test_solve_with_timeout_fails(minizinc_options : MiniZincOptions):
    minizinc_options.time_limit = to_duration(microseconds=1)
                
    result = await best_minizinc_solution(
        """
        include "disjunctive.mzn";
        set of int: TASK = 1..1000;
        set of int: TIME = 1..1000;
                                        
        array[TASK] of var TIME: start;
        array[TASK] of var TIME: duration;

        constraint disjunctive(start, duration);
        """,
        minizinc_options
        )

    assert result.status == SolveStatus.TIMEOUT
