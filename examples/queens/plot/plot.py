from unconstrained.charting import *
from ..model import *

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


def plot(scenario : Scenario) -> Chart:
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