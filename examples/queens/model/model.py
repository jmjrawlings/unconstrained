from unconstrained import *

NAME = 'Queens'
HOME = Path(__file__).parent.parent
INPUT = HOME / 'input'
OUTPUT = HOME / 'output'
DATABASE = OUTPUT / 'queens.db'


Model = db.create_model_class()


class Scenario(Model, table=True):

    # Columns =====================================       
    name : str = db.column()
    n    : int = db.column()

    # Relations ===================================
    queens : List["Queen"] = db.relation("scenario")


class Queen(Model, table=True):

    # Columns =====================================
    number      : int = db.column()
    scenario_id : int = db.foreign_key(Scenario.id)
    row         : int = db.column()
    col         : int = db.column()
    
    # Relations ===================================
    scenario : Scenario = db.relation('queens')


def create_scenario(n=3) -> Scenario:
    """
    Create a Scenario for the given
    number of Queens
    """
    
    scenario = Scenario(n=n, name=f'Queens ({n})')
    for i in range1(n):
        queen = Queen(number=i, row=0, col=0, scenario=scenario)
        scenario.queens.append(queen)
    return scenario