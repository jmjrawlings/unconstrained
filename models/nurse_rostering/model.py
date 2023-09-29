from unconstrained import *
from uuid import UUID as id

@define
class Day(BaseModel):
    day_no : int = int_field()

@define
class Nurse(BaseModel):        
    nurse_no : int = int_field() 

@define
class Shift(BaseModel):
    shift_no : int = int_field()
    day_no : int = int_field()

@define
class ShiftRequest(BaseModel):
    shift_id : id = id_field()
    nurse_id : id = id_field()

@define
class Model(BaseModel):
    days : Seq[Day] = seq_field(Day)
    shifts : Seq[Shift] = seq_field(Shift)
    nurses : Seq[Nurse] = seq_field(Nurse)
    requests : Seq[ShiftRequest] = seq_field(ShiftRequest)



def create(days=3, nurses=4, shifts=3) -> Model:
    from itertools import cycle
            
    model = Model()
    
    for i in range1(nurses):
        nurse = Nurse(nurse_no=i)
        model.nurses.add(nurse)
                            
    for i in range1(days):
        day = Day(day_no=i)
        model.days.add(day)
                
        for i in range1(shifts):
            shift = Shift(shift_no=i, day_no=day.day_no)
            model.shifts.add(shift)
    
    # Generate some initial shift requests
    nurses = cycle(model.nurses)
    for shift in model.shifts:
        nurse = next(nurses)
        request = Request(nurse=nurse, shift=shift, scenario=scenario)
        scenario.requests.append(request)

    log.info(f'{scenario!r} was created')
    return scenario