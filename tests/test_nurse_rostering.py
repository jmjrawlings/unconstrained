from unconstrained import *
from examples import nurse_rostering as ex
from pytest import mark, fixture, param

async def test_solve_with_dynamic_minizinc(minizinc_options):

    engine = db.create_engine(ex.Model)
                        
    with db.session(engine) as session:
        scenario = ex.create_scenario()
            
        async for result in ex.solve_with_minizinc_dynamic(scenario, minizinc_options):
            pass