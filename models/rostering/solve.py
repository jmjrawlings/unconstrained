from unconstrained import *
from unconstrained import minizinc as mz
from .model import Model

async def solve(model : Model, options : mz.SolveOptions):
    """
    Solve the model with minizinc
    """
    
    nurses = model.nurses
    shifts = model.shifts
    days = model.days
    requests = model.requests
    n,s,d,r = [len(x) for x in [nurses, shifts, days, requests]]
                            
    mzn = mz.ModelBuilder()
    mzn.add_section('Nurse Rostering')
    mzn.add_multiline_comment(f'''
    {n} Nurses
    {s} Shifts
    {d} Days
    {r} Requests
    ''')

    for i, nurse in enumerate1(nurses):
        nurse._var = mzn.add_par(type='int', name=f'N{i}', value=i)
        
    for i, shift in enumerate1(shifts):
        shift._var = mzn.add_par(type='int', name=f'S{i}', value=i)

    for i, request in enumerate1(requests):
        request._var = mzn.add_par(type='int', name=f'R{i}', value=i)

    model_string = mzn.string
    async for result in mz.solve(model_string, options=options):
        yield result
