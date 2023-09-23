from unconstrained import *
from examples import queens

async def test_solve(minizinc_options):
        
    result = mz.Result()
                        
    scenario = queens.create_scenario(n=5)
    async for result in queens.solve(scenario, minizinc_options, name=scenario.name, all_solutions=True):
        pass

    chart = queens.plot(scenario)

    ch.save(
        chart, 
        path=queens.OUTPUT / f'{scenario.name}.html',
        width=400,
        height=400,
        title=scenario.name
        )
    assert result.status == mz.ALL_SOLUTIONS