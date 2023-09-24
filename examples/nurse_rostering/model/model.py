from unconstrained import *
from pydantic import BaseModel

HOME = Path(__file__).parent.parent
INPUT = HOME / 'input'
OUTPUT = HOME / 'output'

class M(BaseModel):
    model_id : int
    model : "Model"

class Model(M):    
    days     : List["Day"]         
    shifts   : List["Shift"]     
    nurses   : List["Nurse"]     
    requests : List["ShiftRequest"]

class Day(M):
    day_id : int
    day_no : int

class Nurse(M):
    nurse_id : int             
    nurse_no : int  

class Shift(M):
    shift_id : int               
    shift_no : int
    day_id   : int

class ShiftRequest(M):
    shift_id : int
    nurse_id : int

def create(num_days=3, num_nurses=4, num_shifts=3) -> Model:
    from itertools import cycle
            
    model = Model()

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