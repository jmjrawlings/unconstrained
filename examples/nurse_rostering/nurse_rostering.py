from src import *
from sqlmodel import SQLModel


class Paths:
    """ 
    Filepaths 
    """
        
    home = Path(__file__).parent
    input = home / 'input'
    output = home / 'output'
    database = output / 'nurse_rostering.db'


class Model(SQLModel):
    """
    Convenience class so we don't 
    have to define the primary key over
    and over        
    """
    id : Optional[int] = primary_key()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id) 

class Day(Model, table=True):
    number : int
    shifts : List["Shift"] = backref('day')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('days')


class Nurse(Model, table=True):
    number : int
    shifts: List["Shift"] = backref('nurse')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('nurses')
    requests : List["Request"] = backref('nurse')
    

class Shift(Model, table=True):
    number : int
    day_id : int = foreign_key('day.id')
    day : "Day" = backref('shifts')
    nurse_id : Optional[int] = foreign_key('nurse.id')
    nurse : Optional[Nurse] = backref('shifts')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('shifts')
    requests : List["Request"] = backref('shift')


class Request(Model, table=True):
    shift_id : int = foreign_key('shift.id')
    shift : Shift = backref('requests')
    nurse_id : int = foreign_key('nurse.id')
    nurse : Nurse = backref('requests')
    scenario_id : int = foreign_key('scenario.id')
    scenario : "Scenario" = backref('requests')


class Scenario(Model, table=True):
    days   : List[Day] = backref('scenario')
    shifts : List[Shift] = backref('scenario')
    nurses : List[Nurse] = backref('scenario')
    requests : List[Request] = backref('scenario')


engine = make_engine(path=Paths.database, model=Model)


def create_scenario(
        session,
        num_days=3,
        num_nurses=4,
        num_shifts=3) -> Scenario:

    from itertools import cycle
    
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


async def solve_with_minizinc_dynamic(scenario : Scenario, options : SolveOptions):
    """
    Solve the scenario with a generated MiniZinc model.
    """

    nurses = scenario.nurses
    shifts = scenario.shifts
    days = scenario.days
    requests = scenario.requests
    n,s,d,r = [len(x) for x in [nurses, shifts, days, requests]]
            
    model = MiniZincModelBuilder()
    model.add_section('Nurse Rostering')
    model.add_multiline_comment(f'''
    {n} Nurses
    {s} Shifts
    {d} Days
    {r} Requests
    ''')

    # for i, nurse in enumerate1(nurses):
    #     nurse._var = model.add_par(type='int', name=f'N{i}', value=i)
        
    # for i, shift in enumerate1(shifts):
    #     shift._var = model.add_par(type='int', name=f'S{i}', value=i)

    # for i, request in enumerate1(requests):
    #     request._var = model.add_par(type='int', name=f'R{i}', value=i)

    model_string = model.string
    async for result in solutions(model_string, options=options):
        yield result
        

async def solve_with_minizinc_static(scenario : Scenario, options : SolveOptions):
    """
    Solve the scenario with a static MiniZinc model
    """

    yield Result()

#     model = f"""
#     include "alldifferent.mzn";
    
#     int: d;
#     int: s;
#     int: n;
#     int: r;
    
#     set of int: Day = 1 .. d;
#     set of int: Nurse = 1 .. n;
#     set of int: Shift = 1 .. s;
#     set of int: Request = 1 .. r;
#     set of int: Number = 1 .. 3;
                                                                
#     array[Shift] of Number: shift_number;
#     array[Shift] of Day: shift_day;
#     array[Day, Number] of Shift: shifts;
                            
#     array[Request] of Nurse: request_nurse;
#     array[Request] of Shift: request_shift;

#     array[Shift] of var Nurse: roster;
                        
#     constraint forall (d in Day) (
#         alldifferent([roster[s] | s in shifts[d, ..]])
#     );
    
    
#     """
    
#     options = SolveOptions()
    
#     async for result in solutions(
#         model,
#         options,
#         d = len(scenario.days),
#         n = len(scenario.nurses),
#         s = len(scenario.shifts), 
#         r = len(scenario.requests),
#         shift_number = [s.number for s in scenario.shifts],
#         shift_day = [s.day.number for s in scenario.shifts],
#         shifts = [[s.number for s in d.shifts] for d in scenario.days],
#         request_nurse = [r.nurse.number for r in scenario.requests],
#         request_shift = [r.shift.number for r in scenario.requests],
#         ):
#         yield result
    


def solve_with_ortools(scenario : Scenario) -> Result:
    from ortools.sat.python import cp_model
    
    # Creates the model.
    model = cp_model.CpModel()
    
    # Creates shift variables.
    for s in scenario.shifts:
        var = model.NewBoolVar(f'shift_d{s.day.number}_s{s.number}_n{n.number}')

    return Result()
    
            

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