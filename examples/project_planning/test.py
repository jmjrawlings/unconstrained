from examples.project_planning import *
from pytest import mark, fixture, param

def get_filenames():
    yield param('a_an_example')
    # yield param('b_better_start_small')
    # yield param('c_collaboration')
    # yield param('d_dense_schedule')
    # yield param('e_exceptional_skills')
    # yield param('f_find_great_mentors')
   

@fixture(params=list(get_filenames()))
def filename(request):
    return request.param


@fixture
def filepath(filename):
    filename = f'{filename}.in.txt'
    filepath = input_dir / filename
    return filepath


@fixture
def scenario(filepath) -> Scenario:
    return load_scenario(filepath)
        

async def test_solve_with_static_minizinc(scenario, minizinc_options):

    async for result in solve_with_static_minizinc(scenario, minizinc_options):
        pass

    chart = plot_scenario(scenario, path=output_dir / f'{scenario.name}.vg.html')
    assert result.status.has_solution
        

async def test_solve_with_dynamic_minizinc(scenario, minizinc_options):
    
    async for result in solve_with_dynamic_minizinc(scenario, minizinc_options):
        pass

    chart = plot_scenario(scenario, path = output_dir / f'{scenario.name}.vg.html')
    assert result.status.has_solution


async def test_solve_with_ortools(scenario):
    for result in solve_with_ortools(scenario):
        pass
    