from examples.nurse_rostering import *
from pytest import mark, fixture, param


@fixture
def scenario() -> Scenario:
    return load_scenario()
       

async def test_solve_with_dynamic_minizinc(scenario, minizinc_options):
    
    async for result in solve_with_dynamic_minizinc(scenario, minizinc_options):
        pass
