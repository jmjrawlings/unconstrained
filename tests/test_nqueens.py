from unconstrained import mz, save_chart
from models import nqueens

async def test_nqueens(minizinc_options, tmp_path):
        
    result = mz.SolveResult()
    n = 5                            
    async for result in nqueens.solve(
        n, 
        minizinc_options, 
        name=f"{n} Queens", 
        all_solutions=True
    ):
        pass
    

    # chart = nqueens.plot(scenario)
    
    # save_chart(
    #     chart, 
    #     path=tmp_path / f'{scenario.name}.html',
    #     width=400,
    #     height=400,
    #     title=scenario.name
    #     )
    