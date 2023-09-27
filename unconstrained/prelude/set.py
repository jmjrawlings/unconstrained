from .prelude import flatten
from typing import Generic, Optional, Any, Iterable, TypeVar, Callable, Type, Set as PySet
from itertools import zip_longest

__cache__ = {}

T = TypeVar("T")
U = TypeVar("U")

class Set(Generic[T]):
    """
    A sequence of elements of type T
    """
    optional : bool = False
    type : Type[T]
    data : PySet[T]
            
    def __init__(self, *args):
        self.data = { x for x in self.yield_from(args) }
    
    @classmethod
    def yield_from(cls, args):
        for item in flatten(args):
            if isinstance(item, cls.type):
                yield item
            elif (cls.optional and item is None):
                yield item
            else:
                raise TypeError(f"Could not add {item} of type {type(item)} to sequence of type {cls.type}")

    def add(self, *args):
        """ Add to this list, a mutable operation """
        for item in self.yield_from(args):
            self.data.add(item) 
        return self
        
    def filter(self, f : Callable[[T], bool]) -> "Set[T]":
        """ Filter the sequence with the given function """
        self.__class__(filter(f, self))
        return self
    
    def map(self, f, type: Type[U] = object) -> "Set[U]":
        """ Map the given function of the sequence """
        cls = self.of_type(type)
        seq = cls(map(f, self))
        return seq
        
    def copy(self):
        seq = self.__class__()
        seq.data = self.data.copy()
        return seq

    @staticmethod
    def of_type(t: Type[T]) -> Type["Set[T]"]:

        if t in __cache__:
            return __cache__[t]
        
        class TSeq(Set[T]): #type:ignore 
            type = t #type:ignore

        __cache__[t] = TSeq
        return TSeq

    @property
    def count(self):
        return len(self.data)
    
    def __iadd__(self, other):
        self.add(other)

    def __add__(self, other):
        return self.__class__(self, other)

    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)

    def __str__(self):
        return f"Sequence of {self.count} {self.type.__name__}"
    
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



def set(type: Type[T], *args) -> Set[T]:
    """
    Create a sequence of the given type
    with the arguments provided
    """
    cls = Set.of_type(type)
    seq = cls(args)
    return seq
