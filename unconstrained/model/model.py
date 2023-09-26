"""
model.py

Helper methods for declaring models based on the attrs
library
"""

from ..prelude import *
from attrs import define, field
from uuid import UUID, uuid4
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.period import Period

def uuid_field(**kwargs) -> UUID:
    return field(factory=uuid4, **kwargs)


def int_field(default=0, **kwargs) -> int:
    return field(default=default, converter=to_int, **kwargs)


def string_field(default="", **kwargs) -> str:
    return field(default=default, converter=to_string, **kwargs)


def bool_field(default=False, **kwargs) -> bool:
    return field(default=default, converter=to_bool, **kwargs)


def float_field(default=0.0, **kwargs) -> float:
    return field(default=default, converter=to_float, **kwargs)


def list_field(ty: Type[T], **kwargs) -> List[T]:
    return field(factory=list, converter=to_typed_list(ty), **kwargs)


def set_field(ty: Type[T], **kwargs) -> List[T]:
    return field(factory=set, converter=to_typed_set(ty), **kwargs)


def dict_field(**kwargs):
    return field(factory=dict, **kwargs)


def enum_field(default: E, **kwargs) -> E:
    return field(default = default, converter = to_enum(default.__class__), **kwargs)


def duration_field(default = None) -> Duration:
    defaultValue = to_duration(default)
    return field(default=defaultValue, converter=to_duration)


def datetime_field() -> DateTime:
    return field(factory=to_datetime, converter=to_datetime)


def date_field() -> Date:
    return field(factory=to_date, converter=to_date)


def period_field() -> DateTime:
    return field(factory=to_period, converter=to_period)


@define
class BaseModel:
    """
    Base model class to use
    """
    id : UUID = uuid_field()
