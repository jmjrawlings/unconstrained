from unconstrained import *
from altair import Chart

@attr.s(**ATTRS)
class Queen(HasId):

    # Fields
    id : int = int_field()
    # Solution

    row : int = int_field()
    col : int = int_field()


class Queens(Map[int, Queen]):
    key_type = int
    val_type = Queen


@attr.s(**ATTRS)
class Scenario(HasId):
        
    # Fields
    id : str = uuid_field()
    n : int = int_field()
    queens : Queens = map_field(Queens)
    


def create_scenario(n=3) -> Scenario:
    scenario = Scenario(n=n)
    for i in range(n):
        queen = Queen(id=i+1)
        scenario.queens += queen
    return scenario



async def solve(scenario : Scenario, options : MiniZincOptions, **kwargs):

    model = """
    int: n;
    array [1..n] of var 1..n: q; % queen in column i is in row q[i]

    include "alldifferent.mzn";

    constraint alldifferent(q);                       % distinct rows
    constraint alldifferent([ q[i] + i | i in 1..n]); % distinct diagonals
    constraint alldifferent([ q[i] - i | i in 1..n]); % upwards+downwards

    % search
    solve :: int_search(q, first_fail, indomain_min)
        satisfy;
    """

    async for result in solve_minizinc_model(model, options, n=scenario.n, **kwargs):
        array = result['q']
        q = 0
        for col, row in enumerate(array):
            q += 1
            queen = scenario.queens[q]
            queen.col = col + 1
            queen.row = row + 1
            print(f'{queen} {col} {row}')

        print(result)
    
    yield True
