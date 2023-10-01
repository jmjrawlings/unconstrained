from unconstrained import *

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
    shift_id : Id = id_field()
    nurse_id : Id = id_field()

@define
class Model(BaseModel):
    name : str = str_field()
    days : Seq[Day] = seq_field(Day)
    shifts : Seq[Shift] = seq_field(Shift)
    nurses : Seq[Nurse] = seq_field(Nurse)
    requests : Seq[ShiftRequest] = seq_field(ShiftRequest)

    def __str__(self) -> str:
        return f"Model with {self.nurses.copy} nurses over {self.days.count} days"
    
    def __repr__(self) -> str:
        return f"<{self!s}>"


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
        request = ShiftRequest(shift_id=shift, nurse_id=nurse)
        model.requests.add(request)


    log.info(f'{model} was created')
    return model
