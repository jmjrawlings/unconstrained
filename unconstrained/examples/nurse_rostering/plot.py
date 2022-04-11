from ...prelude import *
import altair as alt
from altair import datum, Chart
from .model import Scenario


def get_records(scenario : Scenario):
    return