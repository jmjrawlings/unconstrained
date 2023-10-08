from .prelude import *
from .seq import Seq
from typing import Generic, TypeVar, Callable, Type, Dict, Literal, LiteralString
from itertools import zip_longest
from uuid import UUID

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")
A = TypeVar("A", bound=LiteralString)
Id = Literal["id"]

class Map(Generic[K,V,A]):
    """
    A mapping from keys to values where the key
    exists as a field stored on the value (eg: item.id)
    """
    key_type  : Type[K]
    val_type  : Type[V]
    key_field : A
    data      : Dict[K, V]
                        
    def __init__(self, key_type: Type[K], val_type: Type[V], key_field: A, *args):
        self.key_type = key_type
        self.val_type = val_type
        self.key_field = key_field
        self.data = {}
        for val in self.gen_values(args):
            key = self.get_key(val)
            self.data[key] = val

    def get_key(self, a):
        return getattr(a, self.key_field)

    def gen_values(self, *args):
        
        def gen(arg):
            if isinstance(arg, self.val_type):
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

        for arg in args:
            yield from gen(arg)         

    def gen_keys(self, *args):

        def gen(arg):
            if isinstance(arg, self.key_type):
                yield arg
            elif isinstance(arg, self.val_type):
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
        return Seq(self.key_type, self.data.keys())

    @property
    def vals(self):
        return Seq(self.val_type, self.data.values())

    def add(self, *args):
        """ Add to this list, a mutable operation """
        for val in self.gen_values(args):
            key = self.get_key(val)
            self.data[key] = val
        return self
        
    def filter(self, f : Callable[[V], bool]) -> "Map[K, V, A]":
        """ Filter the sequence with the given function """
        map = self.create(filter(f, self.vals))
        return map
    
    def to_dict(self, f: Callable[[V],U]=id) -> "Dict[K, U]":
        """ Convert to a dictionary"""
        dict = {k: f(v) for k,v in self.data.items()}
        return dict
        
    def copy(self):
        seq = self.create()
        seq.data = self.data.copy()
        return seq
    
    def parse(self, arg):
        """
        Parse the given value as an instance of this class
        """
        if isinstance(arg, self.__class__):
            if arg.key_type == self.key_type:
                if arg.val_type == self.val_type:
                    return arg
        map = self.create(arg)
        return map
    
    def create(self, *args) -> "Map[K,V,A]":
        map = self.__class__(self.key_type, self.val_type, self.key_field, *args)
        return map

    @property
    def count(self):
        return len(self.data)
    
    @property
    def is_empty(self):
        return not self.data
    
    def __iadd__(self, other):
        self.add(other)

    def __add__(self, other):
        return self.create  (self, other)

    def __iter__(self):
        return iter(self.data.values())
    
    def __len__(self):
        return len(self.data)

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

    def __str__(self):
        v = self.val_type.__name__
        k = self.key_type.__name__
        match self.count:
            case 0:
                return f"Empty Map<{k},{v}>"
            case 1:
                return f"1 {v} by {k}"
            case n:
                return f"{n} {v}s by {k}"
    
    def __repr__(self):
        return f"{self!s}"


def id_map(v: Type[V], *args) -> Map[UUID,V,Id]:
    return Map(UUID, v, "id", *args)
