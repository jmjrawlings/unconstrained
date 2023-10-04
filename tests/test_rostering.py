from unconstrained import *
from models import rostering as m

async def test_nurse_rostering(minizinc_options):

    model = m.create()
    assert True