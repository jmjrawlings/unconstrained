from ...prelude import *

@attr.s(**ATTRS)
class Nurse(HasId):
    # Fields
    nurse_id : int = int_field()

    # Solution
    shift_ids : TList[int] = list_field(int)
        
    # References
    shifts : "Shifts"
    
    def get_id(self):
        return self.nurse_id


class Nurses(Map[int, Nurse]):
    val_type = Nurse


@attr.s(**ATTRS)
class Shift(HasId):
    # Fields
    shift_id : int = int_field()
    shift_no : int = int_field()
    day_id : int = int_field()
    
    # Solution
    nurse_id : int = int_field()

    # References
    day : "Day"
                
    def get_id(self):
        return self.shift_id


class Shifts(Map[int,Shift]):
    val_type = Shift


@attr.s(**ATTRS)
class Day(HasId):
    # Fields
    day_id : int = int_field()
    shift_ids : TList[int] = list_field(int)
    
    # References
    shifts : Shifts
    

class Days(Map[int,Day]):
    val_type = Day

@attr.s(**ATTRS)
class Scenario:
    nurses : Nurses = map_field(Nurses)
    days : Days = map_field(Days)
    shifts : Shifts = map_field(Shifts)



def load_scenario() -> Scenario:
    pass
