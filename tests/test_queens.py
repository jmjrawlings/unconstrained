from src import *
from examples.queens import *
from pytest import fixture


@fixture
def options():
    return SolveOptions()


async def test_solve(options):

    with Session(engine) as session:
        scenario = create_scenario(n=5)
        session.add(scenario)
        session.commit()
        session.refresh(scenario)
                 
        async for result in solve_scenario(scenario, options, name=scenario.name):
            session.commit()
            pass

        session.refresh(scenario)

    chart = plot_scenario(scenario)
    chart = chart.properties(width=400, height=400, title=scenario.name)
    chart.save(Paths.output / f'{scenario.name}.html')
            
    assert result.status == ALL_SOLUTIONS