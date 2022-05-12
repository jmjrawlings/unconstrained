from src import *
from sqlmodel import Field, SQLModel, create_engine, Relationship, Session


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
    number : int
    shifts: List["Shift"] = backref('nurse')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('nurses')
    requests : List["Request"] = backref('nurse')
    
    def __str__(self):
        return f'Nurse {self.number}'

    def __repr__(self):
        return f'<{self!s}>'


class Shift(SQLModel, table=True):
    id : Optional[int] = primary_key()
    number : int
    day_id : int = foreign_key('day.id')
    day : "Day" = backref('shifts')
    nurse_id : Optional[int] = foreign_key('nurse.id')
    nurse : Optional[Nurse] = backref('shifts')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('shifts')
    requests : List["Request"] = backref('shift')

    def __str__(self):
        return f'Shift {self.number} on Day {self.day.number}'

    def __repr__(self):
        return f'<{self!s}>'


class Request(SQLModel, table=True):
    id : Optional[int] = primary_key()
    shift_id : int = foreign_key('shift.id')
    shift : Shift = backref('requests')
    nurse_id : int = foreign_key('nurse.id')
    nurse : Nurse = backref('requests')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('requests')
        
    def __str__(self):
        return f'Request'

    def __repr__(self):
        return f'<{self!s}>'



class Scenario(SQLModel, table=True):
    id : Optional[int] = primary_key()
    days   : List[Day] = backref('scenario')
    shifts : List[Shift] = backref('scenario')
    nurses : List[Nurse] = backref('scenario')
    requests : List[Request] = backref('scenario')
                
    def __str__(self):
        return f'Scenario {self.id}'

    def __repr__(self):
        return f'<{self!s}>'


sqlite_name = "nurse_rostering"
sqlite_url = f"sqlite:///{sqlite_name}.db"
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)


def create_scenario(
        engine=engine,
        num_days=3,
        num_nurses=4,
        num_shifts=3) -> Scenario:

    from itertools import cycle

    with Session(engine) as session:
        scenario = Scenario()

        for i in range1(num_nurses):
            nurse = Nurse(scenario=scenario, number=i)
                        
        for i in range1(num_days):
            day = Day(number=i, scenario=scenario)
            
            for i in range1(num_shifts):
                shift = Shift(number=i, day=day, scenario=scenario)

        session.add(scenario)
        session.commit()
        
        # Generate some initial shift requests
        nurses = cycle(scenario.nurses)
        for shift in scenario.shifts:
            nurse = next(nurses)
            request = Request(nurse=nurse, shift=shift, scenario=scenario)
            session.add(request)

        session.commit()
        
        log.info(f'{scenario!r} was created')

    return scenario


async def solve_with_dynamic_minizinc(scenario : Scenario, options : SolveOptions):
    return
    yield

async def solve_with_minizinc(scenario : Scenario, options : SolveOptions):
    model = f"""
    int: d;
    int: s;
    int: n;

    set of int: Day = 1 .. d;
    set of int: Nurse = 1 .. n;
    set of int: Shift = 1 .. s;

    """

    return
    yield


def solve_with_ortools(scenario : Scenario):
    from ortools.sat.python import cp_model
    
    # Creates the model.
    model = cp_model.CpModel()
    
    # Creates shift variables.
    for s in scenario.shifts:
        var = model.NewBoolVar(f'shift_d{s.day.number}_s{s.number}_n{n.number}')
            

    # # Each shift is assigned to exactly one nurse in .
    # for d in all_days:
    #     for s in all_shifts:
    #         model.AddExactlyOne(shifts[(n, d, s)] for n in all_nurses)

    # # Each nurse works at most one shift per day.
    # for n in all_nurses:
    #     for d in all_days:
    #         model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

    # # Try to distribute the shifts evenly, so that each nurse works
    # # min_shifts_per_nurse shifts. If this is not possible, because the total
    # # number of shifts is not divisible by the number of nurses, some nurses will
    # # be assigned one more shift.
    # min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    # if num_shifts * num_days % num_nurses == 0:
    #     max_shifts_per_nurse = min_shifts_per_nurse
    # else:
    #     max_shifts_per_nurse = min_shifts_per_nurse + 1
    # for n in all_nurses:
    #     num_shifts_worked = 0
    #     for d in all_days:
    #         for s in all_shifts:
    #             num_shifts_worked += shifts[(n, d, s)]
    #     model.Add(min_shifts_per_nurse <= num_shifts_worked)
    #     model.Add(num_shifts_worked <= max_shifts_per_nurse)

    # # pylint: disable=g-complex-comprehension
    # model.Maximize(
    #     sum(shift_requests[n][d][s] * shifts[(n, d, s)] for n in all_nurses
    #         for d in all_days for s in all_shifts))

    # # Creates the solver and solve.
    # solver = cp_model.CpSolver()
    # status = solver.Solve(model)

    # if status == cp_model.OPTIMAL:
    #     print('Solution:')
    #     for d in all_days:
    #         print('Day', d)
    #         for n in all_nurses:
    #             for s in all_shifts:
    #                 if solver.Value(shifts[(n, d, s)]) == 1:
    #                     if shift_requests[n][d][s] == 1:
    #                         print('Nurse', n, 'works shift', s, '(requested).')
    #                     else:
    #                         print('Nurse', n, 'works shift', s,
    #                               '(not requested).')
    #         print()
    #     print(f'Number of shift requests met = {solver.ObjectiveValue()}',
    #           f'(out of {num_nurses * min_shifts_per_nurse})')
    # else:
    #     print('No optimal solution found !')




import altair as alt
from altair import datum, Chart

def plot_scenario(
        scenario : Scenario,
        solutions=[], 
        width = 600, 
        path : Optional[Path] = None) -> Chart:
    return Chart()