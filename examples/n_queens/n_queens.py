from src import *
import altair as alt
from altair import Chart
import pandas as pd

class Queen(SQLModel, table=True):
    id : Optional[int] = primary_key()
    number : int
    scenario_id : int = foreign_key("scenario.id")
    scenario : "Scenario" = backref('queens')
    row : int
    col : int


class Scenario(SQLModel, table=True):
    id : Optional[int] = primary_key()
    name : str
    n : int
    queens : List["Queen"] = backref("scenario")
        
    def __str__(self):
        return self.name

engine = make_engine()

def make_session(engine=engine):
    return Session(engine)


def create_scenario(session : Session, n=3) -> Scenario:
    scenario = Scenario(n=n, name=f'{n} Queens')
    session.add(scenario)
    for i in range1(n):
        queen = Queen(number=i, row=0, col=0, scenario=scenario)
        session.add(queen)
    session.commit()    
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
