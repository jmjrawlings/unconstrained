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