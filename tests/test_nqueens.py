from src import *
from examples.n_queens import *
from pytest import fixture


@fixture
def options():
    return SolveOptions()

@fixture
def session():
    with Session(engine) as s:
        yield s


async def test_solve(session, options, output_dir):
    scenario = create_scenario(session, n=5)
    
    async for result in solve_scenario(scenario, options, name=scenario.name):
        session.commit()
        pass

    chart = plot_scenario(scenario)
    chart = chart.properties(width=400, height=400, title=scenario.name)
    chart.save(output_dir / f'{scenario.name}.html')
        
    assert result.status == ALL_SOLUTIONS