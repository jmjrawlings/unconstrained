from unconstrained import *
from unconstrained import minizinc as mz
from .model import Model

async def solve(model : Model, options : mz.SolveOptions, **kwargs):
    """
    Solve the scenario with the given options
    """
            
    mzn = f"""
    % N-Queens satisfaction model
    include "alldifferent.mzn";
        
    int: n = {model.n};

    set of int: N = 1 .. n;

    % The Queen in column i is in row q[i]
    array [N] of var N: q; 
            
    constraint % Each queen is in a different row
        alldifferent(q); 

    constraint % Upwards diagonal
        alldifferent([ q[i] + i | i in N]); 

    constraint % Downwards diagonal
        alldifferent([ q[i] - i | i in N]); 
    
    solve ::
        int_search(q, first_fail, indomain_min)
        satisfy;
    """

    async for result in mz.solve(mzn, options, **kwargs):
        
        if not result.has_solution:
            yield result
            continue

        array = result['q']
        for i, row in enumerate(array):
            queen = model.queens[i]
            queen.col = i + 1
            queen.row = row

        yield result