from ..prelude import *
import altair as alt
from altair import Chart

def save(chart : Chart, path : Path, **properties) -> Path:
    """
    Save the given chart to the path, applying all
    properties given
    """
    chart = chart.properties(**properties)
    chart.save(path)
    return path