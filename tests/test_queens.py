from src import *
from examples import queens
from pytest import fixture

@fixture
def options():
    return mz.SolveOptions()


async def test_solve(options):

    result = mz.Result()
        
    with db.Session(queens.engine) as session:
        scenario = queens.create_scenario(n=5)
        session.add(scenario)
        session.commit()
        session.refresh(scenario)
                 
        async for result in queens.solve(scenario, options, name=scenario.name):
            session.commit()

        session.refresh(scenario)

    chart = queens.plot(scenario)
    
    charting.save(
        chart, 
        path=queens.OUTPUT / f'{scenario.name}.html',
        width=400,
        height=400,
        title=scenario.name
        )
    assert result.status == mz.ALL_SOLUTIONS