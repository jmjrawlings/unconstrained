import h2o_wave as wave
from ..model import model
from ..plot import plot
from ..solve import solve
from unconstrained import *


@wave.app(f'/{model.NAME}')
async def serve(q: wave.Q):
       
    await q.page.save()