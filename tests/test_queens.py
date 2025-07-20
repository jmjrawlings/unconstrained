from unconstrained import mz, save_chart
from models import queens

async def test_solve(minizinc_options, tmp_path):
        
    result = mz.Result()
                            
    scenario = queens.create(n=5)
    async for result in queens.solve(scenario, minizinc_options, name=scenario.name, all_solutions=True):
        pass

    chart = queens.plot(scenario)
    
    save_chart(
        chart, 
        path=tmp_path / f'{scenario.name}.html',
        width=400,
        height=400,
        title=scenario.name
        )
    assert result.status == mz.ALL_SOLUTIONS