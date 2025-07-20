from unconstrained import mz
from .model import Model

async def solve(model : Model, options : mz.SolveOptions, **kwargs):
    """
    Solve the model with the given options
    """
            
    mzn = f"""
    % N-Queens satisfaction model
    include "alldifferent.mzn";
        
    int: n = {model.n};

    set of int: N = 1 .. n;

    % The Queen in column i is in row q[i]
    array [N] of var N: q; 
            
    % Each queen is in a different row
    constraint 
        alldifferent(q); 

    % Upwards diagonal
    constraint 
        alldifferent([ q[i] + i | i in N]); 

    % Downwards diagonal
    constraint 
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
            queen = model.queens.get(i)
            queen.col = i + 1
            queen.row = row

        yield result