from unconstrained import *
from examples.n_queens import *
from pytest import fixture

@fixture
def scenario():
    return create_scenario(5)

@fixture
def options():
    return MiniZincOptions()


async def test_solve(scenario, options):
            
    async for result in solve(scenario, options, name='N Queens'):
        pass

    assert result