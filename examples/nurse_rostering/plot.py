from unconstrained import *
import altair as alt
from altair import datum, Chart
from .model import Scenario

def plot_scenario(
        scenario : Scenario,
        solutions=[], 
        width = 600, 
        path : Optional[Path] = None) -> Chart:
    return Chart()