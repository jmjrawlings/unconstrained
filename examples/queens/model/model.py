from src import *

NAME = 'Queens'
HOME = Path(__file__).parent.parent
INPUT = HOME / 'input'
OUTPUT = HOME / 'output'
DATABASE = OUTPUT / 'queens.db'


class Model(db.Model):
    metadata = db.MetaData()


class Scenario(Model, table=True):
    name : str = db.column()
    n    : int = db.column()

    queens : List["Queen"] = db.backref("scenario")


class Queen(Model, table=True):
    number      : int = db.column()
    scenario_id : int = db.foreign_key("scenario.id")
    row         : int = db.column()
    col         : int = db.column()
    
    scenario : "Scenario" = db.backref('queens')


engine = db.make_engine(path=DATABASE, model=Model)


def create_scenario(n=3) -> Scenario:
    scenario = Scenario(n=n, name=f'{n} Queens')
    for i in range1(n):
        queen = Queen(number=i, row=0, col=0, scenario=scenario)
        scenario.queens.append(queen)
    return scenario