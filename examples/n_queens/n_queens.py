from unconstrained import *
import altair as alt
from altair import Chart
import pandas as pd


@attr.s(**ATTRS)
class Queen(HasId):
    id  : int = int_field()
    row : int = int_field(comment='Row (filled by solver)')
    col : int = int_field(comment='Column (filled by solver)')
    

Queens = map_type(int, Queen)

@attr.s(**ATTRS)
class Scenario(HasId):
    id  : str = uuid_field()
    n   : int = int_field(comment='Size of the Scenario')
    queens : Queens = map_field(Queens)
    
    @property
    def name(self):
        return f'{self.n} Queens'

    def __str__(self):
        return self.name
    


def create_scenario(n=3) -> Scenario:
    scenario = Scenario(n=n)
    for i in range(n):
        queen = Queen(id=i+1)
        scenario.queens += queen
    return scenario



async def solve_scenario(scenario : Scenario, options : SolveOptions, **kwargs):

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

    async for result in solutions(model, options, n=scenario.n, **kwargs):
        array = result['q']
        q = 0
        for col, row in enumerate(array):
            q += 1
            queen = scenario.queens[q]
            queen.col = col + 1
            queen.row = row

        yield result


def dataset(scenario : Scenario):
    records = []
    for queen in scenario.queens:
        records.append(dict(
            n = scenario.n,
            queen = queen.id,
            row = queen.row,
            col = queen.col
        ))
    df = pd.DataFrame.from_records(records)
    return df


def plot(scenario : Scenario) -> Chart:
    data = dataset(scenario)
    base = (alt
        .Chart(data)
        .encode(x=alt.X('col:O'))
        .encode(y=alt.Y('row:O'))
    )

    rects = base.mark_rect(color='black').encode()
    texts = base.mark_text(color='white', size=14).encode(text='queen:N')
    chart = rects + texts
    return chart
