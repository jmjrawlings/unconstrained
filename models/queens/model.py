from unconstrained import (
    BaseModel,
    define,
    int_field,
    str_field,
    seq_field,
    Seq,
    range1
)

@define
class Queen(BaseModel):
    number : int = int_field()
    row : int = int_field()
    col : int = int_field()
    

@define
class Model(BaseModel):
    name : str = str_field("Queens")
    n : int = int_field(5)
    queens : Seq[Queen] = seq_field(Queen)


def create(n=3) -> Model:
    """
    Create a model for the given
    number of Queens
    """
    
    model = Model(n=n, name=f'Queens ({n})', queens=[])
    for i in range1(n):
        queen = Queen(number=i)
        model.queens.add(queen)
    return model