from unconstrained import *

HOME = Path(__file__).parent.parent
INPUT = HOME / 'input'
OUTPUT = HOME / 'output'
DATABASE = OUTPUT / 'nurse_rostering.db'


Model = db.create_model_class()


class Scenario(Model, table=True):
    days : List["Day"]         = db.relation('scenario')
    shifts : List["Shift"]     = db.relation('scenario')
    nurses : List["Nurse"]     = db.relation('scenario')
    requests : List["Request"] = db.relation('scenario')


class Day(Model, table=True):
    number : int           = db.column()
    shifts : List["Shift"] = db.relation('day')
    scenario_id : int      = db.foreign_key(Scenario.id)
    scenario : "Scenario"  = db.relation('days')


class Nurse(Model, table=True):
    number : int
    shifts: List["Shift"]      = db.relation('nurse')
    scenario_id : int          = db.foreign_key(Scenario.id)
    scenario : "Scenario"      = db.relation(Scenario.nurses)
    requests : List["Request"] = db.relation('nurse')
    

class Shift(Model, table=True):
    number : int               = db.column()
    day_id : int               = db.foreign_key(Day.id)
    day : "Day"                = db.relation(Day.shifts)
    nurse_id : Optional[int]   = db.foreign_key(Nurse.id)
    nurse : Optional[Nurse]    = db.relation(Nurse.shifts)
    scenario_id : int          = db.foreign_key(Scenario.id)
    scenario : "Scenario"      = db.relation(Scenario.shifts)
    requests : List["Request"] = db.relation('shift')


class Request(Model, table=True):
    shift_id : int        = db.foreign_key(Shift.id)
    shift : Shift         = db.relation(Shift.requests)
    nurse_id : int        = db.foreign_key(Nurse.id)
    nurse : Nurse         = db.relation(Nurse.requests)
    scenario_id : int     = db.foreign_key(Scenario.id)
    scenario : "Scenario" = db.relation(Scenario.requests)


def create_scenario(
        num_days=3,
        num_nurses=4,
        num_shifts=3) -> Scenario:

    from itertools import cycle
    
    scenario = Scenario()

    for i in range1(num_nurses):
        nurse = Nurse(scenario=scenario, number=i)
        scenario.nurses.append(nurse)
                            
    for i in range1(num_days):
        day = Day(number=i, scenario=scenario)
        scenario.days.append(day)
        
        for i in range1(num_shifts):
            shift = Shift(number=i, day=day, scenario=scenario)
            scenario.shifts.append(shift)
    
    # Generate some initial shift requests
    nurses = cycle(scenario.nurses)
    for shift in scenario.shifts:
        nurse = next(nurses)
        request = Request(nurse=nurse, shift=shift, scenario=scenario)
        scenario.requests.append(request)

    log.info(f'{scenario!r} was created')
    return scenario