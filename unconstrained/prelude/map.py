from .prelude import flatten
from .seq import seq
from typing import Generic, Optional, Any, Iterable, TypeVar, Callable, Type, Dict
from itertools import zip_longest
from uuid import UUID

__cache__ = {}

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")

class Map(Generic[K,V]):
    """
    A mapping from keys to values where the key
    exists as a field stored on the value (eg: item.id)
    """
    key_type : Type[K]
    val_type : Type[V]
    get_key  : Callable[[V],K]
    data     : Dict[K, V]
                    
    def __init__(self, *args):
        self.data = {}
        for val in self.gen_values(args):
            key = self.get_key(val)
            self.data[key] = val
    
    @classmethod
    def gen_values(cls, *args):
        
        def gen(arg):
            if isinstance(arg, cls.val_type):
                yield arg
            elif isinstance(arg, dict):
                yield from gen(arg.values())
            elif hasattr(arg, '__iter__'):
                if isinstance(arg, str):
                    raise TypeError(arg)
                else:                
                    for a in arg:
                        yield from gen(a)
            elif callable(arg):
                yield from gen(arg())
            else:
                raise TypeError(arg)
            
        yield from gen(args)            

    @classmethod
    def gen_keys(cls, *args):

        def gen(arg):
            if isinstance(arg, cls.key_type):
                yield arg
            elif isinstance(arg, cls.val_type):
                yield cls.get_key(arg) #type:ignore
            elif hasattr(arg, '__iter__'):
                if isinstance(arg, str):
                    raise TypeError(arg)
                else:                
                    for a in arg:
                        yield from gen(a)
            elif callable(arg):
                yield from gen(arg())
            else:
                raise TypeError(arg)
            
        yield from gen(args)

    @property
    def keys(self):
        return seq(self.key_type, self.data.keys())

    @property
    def vals(self):
        return seq(self.val_type, self.data.values())

    def add(self, *args):
        """ Add to this list, a mutable operation """
        for val in self.gen_values(args):
            key = self.get_key(val)
            self.data[key] = val
        return self
        
    def filter(self, f : Callable[[V], bool]) -> "Map[K, V]":
        """ Filter the sequence with the given function """
        map = self.__class__(filter(f, self.vals))
        return map
    
    def to_dict(self, f: Callable[[V],U]=id) -> "Dict[K, U]":
        """ Convert to a dictionary"""
        dict = {k: f(v) for k,v in self.data.items()}
        return dict
        
    def copy(self):
        seq = self.__class__()
        seq.data = self.data.copy()
        return seq

    @staticmethod
    def from_id(v: Type[V]):
        return Map.module(UUID, v, get_id)

    @staticmethod
    def module(k: Type[K], v: Type[V], get_key) -> Type["Map[K,V]"]:
        uid = hash((k,v, get_key))
        if uid in __cache__:
            return __cache__[uid]
        
        def get(_, v):
            return get_key(v)
        
        class Module(Map[K,V]):  # type:ignore
            key_type = k         # type:ignore
            val_type = v         # type:ignore
            get_key  = get       # type:ignore

        __cache__[uid] = Module
        return Module

    @property
    def count(self):
        return len(self.data)
    
    def __iadd__(self, other):
        self.add(other)

    def __add__(self, other):
        return self.__class__(self, other)

    def __iter__(self):
        return iter(self.data.values())
    
    def __len__(self):
        return len(self.data)

    def __str__(self):
        return f"<Map from {self.key_type.__name__} to {self.count} {self.val_type.__name__}>"
    
    def __eq__(self, other):
        if id(self) == id(other):
            return True
        try:
            for a,b in zip_longest(self, other):
                if a != b:
                    return False
            return True                
        except:
            return False


def map(k: Type[K], v: Type[V], get_key, *args) -> Map[K, V]:
    """
    Create a sequence of the given type
    with the arguments provided
    """
    cls = Map.module(k, v, get_key)
    seq = cls(args)
    return seq

def get_id(x):
    return x.id

def id_map(k: Type[K], v: Type[V], *args) -> Map[K,V]:
    return map(k, v, get_id, *args)