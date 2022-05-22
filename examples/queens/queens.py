from src import *
import altair as alt
from altair import Chart
import pandas as pd


class Paths:
    """ Filepaths """
    
    home = Path(__file__).parent
    input = home / 'input'
    output = home / 'output'
    database = output / 'queens.db'


class Model(SQLModel):
    metadata = MetaData()
    
    """
    Convenience class so we don't 
    have to define the primary key over
    and over        
    """
    id : Optional[int] = primary_key()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)    


class Scenario(Model, table=True):
    name : str
    n : int
    queens : List["Queen"] = backref("scenario")


class Queen(Model, table=True):
    number : int
    scenario_id : int = foreign_key("scenario.id")
    scenario : "Scenario" = backref('queens')
    row : int
    col : int


engine = make_engine(path=Paths.database, model=Model)


def create_scenario(n=3) -> Scenario:
    scenario = Scenario(n=n, name=f'{n} Queens')
    for i in range1(n):
        queen = Queen(number=i, row=0, col=0, scenario=scenario)
        scenario.queens.append(queen)
    return scenario


async def solve_scenario(scenario : Scenario, options : SolveOptions, **kwargs):
    
    model = f"""
    % N-Queens satisfaction model
    include "alldifferent.mzn";
        
    int: n = {scenario.n};

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

    async for result in solutions(model, options, **kwargs):
        array = result['q']
        for i, row in enumerate(array):
            queen = scenario.queens[i]
            queen.col = i + 1
            queen.row = row
            log.info(f'Queen {queen.number} at ({queen.row}, {queen.col})')

        yield result


def create_chart_data(scenario : Scenario):
    records = []
    for queen in scenario.queens:
        records.append(dict(
            n = scenario.n,
            queen = queen.number,
            y = queen.row,
            y2 = queen.row + 1,
            x = queen.col,
            x2 = queen.col + 1
        ))
    df = pd.DataFrame.from_records(records)
    return df


def plot_scenario(scenario : Scenario) -> Chart:
    data = create_chart_data(scenario)
    base = (alt
        .Chart(data)
        .encode(x=alt.X('x:O', axis=alt.Axis(grid=True, labels=False)))
        .encode(y=alt.Y('y:O', axis=alt.Axis(grid=True, labels=False)))
        .encode(x2=alt.X2('x2:O'))
        .encode(y2=alt.Y2('y2:O'))
    )
    
    rects = base.mark_rect(color='black')
    texts = base.mark_text(color='white', size=14).encode(text='queen:N')
    chart = rects + texts
    return chart