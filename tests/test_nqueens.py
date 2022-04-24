from unconstrained import *
from examples.n_queens import *
from pytest import fixture


@fixture
def scenario():
    return create_scenario(5)


@fixture
def options():
    return SolveOptions()



async def test_solve(scenario : Scenario, options, output_dir):
                
    async for result in solve_scenario(scenario, options, name=scenario.name):
        pass

    chart = plot(scenario)
    chart = chart.properties(width=400, height=400, title=scenario.name)
    chart.save(output_dir / f'{scenario.name}.html')
        
    assert result.status == FEASIBLE