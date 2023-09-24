from unconstrained import *
from pydantic import BaseModel
from uuid import UUID, uuid4

NAME = 'Queens'
HOME = Path(__file__).parent.parent
INPUT = HOME / 'input'
OUTPUT = HOME / 'output'

class M(BaseModel):
    model_id : UUID
    model : "Model" 

class Model(M):
    name : str
    n    : int
    queens : List["Queen"]

class Queen(M):
    queen_id : UUID
    number   : int
    row      : int
    col      : int

def create(n=3) -> Model:
    """
    Create a model for the given
    number of Queens
    """
    
    model = Model(n=n, name=f'Queens ({n})', queens=[])
    for i in range1(n):
        queen = Queen(number=i, row=0, col=0, scenario=scenario)
        scenario.queens.append(queen)
    return scenario