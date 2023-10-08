"""
model.py

Helper methods for declaring models based on the attrs
library
"""

from ..prelude import *
import attrs
import json
from attrs import define, field
from cattrs.preconf.json import make_converter
from uuid import UUID, uuid4
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.period import Period
from typing import Type, TypeVar, Any, get_origin


M = TypeVar("M", bound="BaseModel")


def id_field(**kwargs) -> UUID:
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
    
    def factory():
        return Seq(ty)
    
    empty = factory()    
    
    def convert(obj):
        return empty.parse(obj)
    
    return field(factory=factory, converter=convert, **kwargs)



def map_field(key_type: Type[K], val_type: Type[V], key_field : A, **kwargs) -> Map[K,V,A]:
    
    def factory():
        return Map(key_type, val_type, key_field)
    
    empty = factory()
            
    def convert(obj):
        return empty.parse(obj)

    return field(factory=factory, converter=convert, **kwargs)


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


def optional(f, **kwargs):
    default = kwargs.pop('default', f._default)
        
    def converter(v):
        if v is None:
            return 
        return f.converter(v)

    return field(default=default, converter=converter)


json_converter = make_converter()

def register_datetime():

    from pendulum.parser import parse

    def unstructure(dt: DateTime):
        return dt.to_iso8601_string()

    def structure(s: str, _):
        dt = parse(s)
        if isinstance(dt, DateTime):
            return dt
        raise ValueError(s)
    
    json_converter.register_unstructure_hook(DateTime, unstructure)
    json_converter.register_structure_hook(DateTime, structure)

    
def register_uuid():

    def unstructure(id: UUID):
        return id.hex
    
    def structure(payload, _):
        id = UUID(payload)
        return id

    json_converter.register_unstructure_hook(UUID, unstructure)
    json_converter.register_structure_hook(UUID, structure)


def register_seq():
    
    def typecheck(cls: Type):
        if get_origin(cls) == Seq:
            return True
        return False
  
       
    def structure(cls: Type[Seq]):
                        
        t : Type = cls.__args__[0] #type:ignore
                        
        def f(payload, c: Type[Seq]):  
            seq = c(t)
            for record in payload:
                item = json_converter.structure(record, t)
                seq.add(item)
            return seq
        
        return f
        
    def unstructure(cls: Type[Seq]):
        
        def f(seq: Seq):
            payload = json_converter.unstructure(seq.data, list)
            return payload
        
        return f
        
    json_converter.register_structure_hook_factory(typecheck, structure)
    json_converter.register_unstructure_hook_factory(typecheck, unstructure)


def register_map():
            
    def typecheck(cls: Type):
        if get_origin(cls) == Map:
            return True
        return False
    
    def structure(cls: Type[Map]):
        # eg: Map[UUID, Item, Id]                
        type_args = cls.__args__ # type:ignore
        key_type = type_args[0]
        val_type = type_args[1]
        key_field = type_args[2].__args__[0]
                
        def f(payload: dict, cls: Type[Map]):
            map = cls(key_type, val_type, key_field)
            for k,v in payload.items():
                item = json_converter.structure(v, val_type)
                map.add(item)
            return map
        
        return f
        
    def unstructure(cls: Type[Map]):
                
        def f(map: Map):
            payload = json_converter.unstructure(map.data, dict)
            return payload
        
        return f
        
    json_converter.register_structure_hook_factory(typecheck, structure)
    json_converter.register_unstructure_hook_factory(typecheck, unstructure)


register_datetime()
register_uuid()
register_seq()
register_map()


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
        payload = json_converter.unstructure(self)
        return payload
    

    def to_json_string(self, **kwargs) -> str:
        """
        Serialize this model as a JSON string
        """
        payload = json_converter.dumps(self, **kwargs)
        return payload

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
            return json_converter.structure(dict, cls)
        except Exception as e:
            raise e
        

    @classmethod
    def from_json_string(cls: Type[M], string: str) -> M:
        """
        Create an object of this type from a json string
        """
        model = json_converter.loads(string,cls)
        return model


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
        payload = self.to_json_string()
        instance = self.from_json_string(payload)
        return instance