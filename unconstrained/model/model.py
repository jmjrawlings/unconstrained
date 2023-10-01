"""
model.py

Helper methods for declaring models based on the attrs
library
"""

from ..prelude import *
import attrs
from attrs import define, field
from cattrs import Converter
from uuid import UUID as Id, uuid4
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.period import Period
from typing import Type, Callable, TypeVar

M = TypeVar("M", bound="BaseModel")


def id_field(**kwargs) -> Id:
    return field(factory=uuid4, converter=to_id, **kwargs)


def int_field(default=0, **kwargs) -> int:
    return field(default=default, converter=to_int, **kwargs)


def str_field(default="", **kwargs) -> str:
    return field(default=default, converter=to_string, **kwargs)


def bool_field(default=False, **kwargs) -> bool:
    return field(default=default, converter=to_bool, **kwargs)


def float_field(default=0.0, **kwargs) -> float:
    return field(default=default, converter=to_float, **kwargs)


def seq_field(ty: Type[T], **kwargs) -> Seq[T]:
    cls = Seq.module(ty)
    return field(factory=cls, converter=cls.parse, **kwargs)


def map_field(val_type: Type[V], key_type: Type[K] = Id, get_key: Callable[[V], K] = dot.id, **kwargs) -> Map[K,V]:
    cls = Map.module(key_type, val_type, get_key)
    return field(factory=cls, converter=cls.parse, **kwargs)


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


def period_field() -> Period:
    return field(factory=to_period, converter=to_period)


converter = Converter()

@define
class BaseModel:
    """
    Base model class to use
    """
    id = id_field()
    

    def to_dict(self) -> dict:
        """
        Convert this model to a dictionary
        """
        payload = converter.unstructure(self)
        return payload
    

    def to_json_string(self, **kwargs) -> str:
        """
        Serialize this model as a JSON string
        """
        payload = self.to_dict()
        string = json.dumps(payload, **kwargs)
        return string
    

    def to_file(self, path, **kwargs) -> Path:
        """
        Serialize this model as a JSON file
        """
        path = to_filepath(path)
        string = self.to_json_string(**kwargs)
        t0 = now()
        path.write_text(string)
        print(f'write "{type(self).__name__}" -> {path} completed in {elapsed_since(t0)}')
        return path
    
    
    @classmethod
    def from_dict(cls: Type[M], dict) -> M:
        """
        Create an instance of this class from the
        given dictionary
        """
        try:
            return converter.structure(dict, cls)
        except Exception as e:
            raise e
        

    @classmethod
    def from_json_string(cls: Type[M], string: str) -> M:
        """
        Create an object of this type from a json string
        """
        dict = json.loads(string)
        return cls.from_dict(dict)


    @classmethod
    def from_file(cls: Type[M], path) -> M:
        """
        Deserialize the object from the given filepath
        """

        t = now()
        path = to_existing_filepath(path)
        text = path.read_text()
        instance = cls.from_json_string(text)
        print(f'loaded "{cls.__name__}" from {path} in {elapsed_since(t)}')
        return instance
    

    def copy(self):
        """
        Create a deep copy of this object - no references are shared
        """
        payload = self.to_dict()
        instance = self.from_dict(payload)
        return instance
    