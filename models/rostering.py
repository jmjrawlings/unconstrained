# Nurse Rostering
# Taken from https://developers.google.com/optimization/scheduling/employee_scheduling

from unconstrained import enumerate1, range1
from unconstrained import minizinc as mz
from unconstrained import Seq, UUID, int_field, id_field, BaseModel, define, str_field, seq_field


@define
class Day(BaseModel):
    day_no: int = int_field()


@define
class Nurse(BaseModel):
    nurse_no: int = int_field()


@define
class Shift(BaseModel):
    shift_no: int = int_field()
    day_no: int = int_field()


@define
class ShiftRequest(BaseModel):
    shift_id: UUID = id_field()
    nurse_id: UUID = id_field()


@define
class Model(BaseModel):
    name: str = str_field()
    days: Seq[Day] = seq_field(Day)
    shifts: Seq[Shift] = seq_field(Shift)
    nurses: Seq[Nurse] = seq_field(Nurse)
    requests: Seq[ShiftRequest] = seq_field(ShiftRequest)

    def __str__(self) -> str:
        return f"Model with {self.nurses.copy} nurses over {self.days.count} days"

    def __repr__(self) -> str:
        return f"<{self!s}>"
    

def create_model(days=3, nurses=4, shifts=3) -> Model:
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

    return model


async def solve(model: Model, options: mz.SolveOptions):
    """
    Solve the model with minizinc
    """

    nurses = model.nurses
    shifts = model.shifts
    days = model.days
    requests = model.requests
    n, s, d, r = [len(x) for x in [nurses, shifts, days, requests]]

    mzn = mz.ModelBuilder()
    mzn.add_section("Nurse Rostering")
    mzn.add_multiline_comment(f"""
    {n} Nurses
    {s} Shifts
    {d} Days
    {r} Requests
    """)

    for i, nurse in enumerate1(nurses):
        nurse._var = mzn.add_par(type="int", name=f"N{i}", value=i)

    for i, shift in enumerate1(shifts):
        shift._var = mzn.add_par(type="int", name=f"S{i}", value=i)

    for i, request in enumerate1(requests):
        request._var = mzn.add_par(type="int", name=f"R{i}", value=i)

    model_string = mzn.string
    async for result in mz.solve(model_string, options=options):
        yield result
