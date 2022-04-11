"""
Solve the scenario using a dynamically generated minizinc model
"""

from .model import *
from ...minizinc import *

async def solve_with_dynamic_minizinc(scenario : Scenario, options : MiniZincOptions):
    return
