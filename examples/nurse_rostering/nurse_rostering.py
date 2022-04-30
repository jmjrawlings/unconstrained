from unconstrained import *
from sqlmodel import Field, SQLModel, create_engine, Relationship, Session

sqlite_name = "database"
sqlite_url = f"sqlite:///{sqlite_name}.db"


def primary_key(**kwargs):
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    return Field(default=None, foreign_key=key, **kwargs)


def backref(name, **kwargs):
    return Relationship(back_populates=name, **kwargs)

class Day(SQLModel, table=True):
    id : Optional[int] = primary_key()
    number : int
    shifts : List["Shift"] = backref('day')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('days')


class Nurse(SQLModel, table=True):
    id : Optional[int] = primary_key()
    shifts: List["Shift"] = backref('nurse')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('nurses')
        

class Shift(SQLModel, table=True):
    id : Optional[int] = primary_key()
    number : int
    day_id : int = foreign_key('day.id')
    day : "Day" = backref('shifts')
    nurse_id : Optional[int] = foreign_key('nurse.id')
    nurse : Optional[Nurse] = backref('shifts')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('shifts')


class Scenario(SQLModel, table=True):
    id : Optional[int] = primary_key()
    days   : List[Day] = backref('scenario')
    shifts : List[Shift] = backref('scenario')
    nurses : List[Nurse] = backref('scenario')

engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)


def load_scenario(engine=engine) -> Scenario:
    with Session(engine) as session:
        scenario = Scenario()
                
        for i in range(1, 4):
            day = Day(number=i, scenario=scenario)
            scenario.days.append(day)

        session.add(scenario)
        session.commit()
        
    return scenario


async def solve_with_dynamic_minizinc(scenario : Scenario, options : SolveOptions):
    return
    yield


import altair as alt
from altair import datum, Chart

def plot_scenario(
        scenario : Scenario,
        solutions=[], 
        width = 600, 
        path : Optional[Path] = None) -> Chart:
    return Chart()