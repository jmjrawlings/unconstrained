from unconstrained import *
from examples import queens
from pytest import fixture

async def test_solve(minizinc_options):
        
    result = mz.Result()
    engine = db.create_engine(queens.Model)
                        
    with db.session(engine) as session:
        scenario = queens.create_scenario(n=5)
        session.add(scenario)
        session.commit()
        session.refresh(scenario)
                 
        async for result in queens.solve(scenario, minizinc_options, name=scenario.name):
            session.commit()

        session.refresh(scenario)
        chart = queens.plot(scenario)

    ch.save(
        chart, 
        path=queens.OUTPUT / f'{scenario.name}.html',
        width=400,
        height=400,
        title=scenario.name
        )
    assert result.status == mz.ALL_SOLUTIONS