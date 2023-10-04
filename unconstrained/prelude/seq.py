from .prelude import *
from typing import Generic, Any, TypeVar, List
from itertools import zip_longest

__cache__ = {}

def flatten(*args):
    """
    Flatten the given arguments by yielding individual
    elements
    """
    def items(arg):
        if hasattr(arg, 'items'):
            yield from items(arg.items)
        elif hasattr(arg, '__iter__'):
            if isinstance(arg, str):
                yield arg
            else:                
                for a in arg:
                    yield from items(a)
        elif callable(arg):
            yield from items(arg())
        else:
            yield arg

    yield from items(args)
    


class Seq(Generic[T]):
    """
    A sequence of elements of type T
    """
    optional : bool = False
    type : Type[T]
    data : List[T]
        
    def __init__(self, *args):
        self.data = []
        for item in self.yield_from(args):
            self.data.append(item)
    
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
            self.data.append(item) 
        return self
        
    def filter(self, f : Callable[[T], bool]) -> "Seq[T]":
        """ Filter the sequence with the given function """
        self.__class__(filter(f, self))
        return self
    
    def map(self, f, type: Type[U] = object) -> "Seq[U]":
        """ Map the given function of the sequence """
        cls = self.module(type)
        seq = cls(map(f, self))
        return seq
        
    def copy(self):
        seq = self.__class__()
        seq.data = self.data.copy()
        return seq

    @staticmethod
    def module(t: Type[T]) -> Type["Seq[T]"]:
        """
        Create or return the class representing
        a sequence of type T
        """

        if t in __cache__:
            return __cache__[t]
        
        class Sequence(Seq[T]): #type:ignore 
            type = t #type:ignore

        __cache__[t] = Sequence
        return Sequence

    @staticmethod
    def list(*args) -> "Seq[Any]":
        """
        Create an untyped sequence from
        the given arguments
        """
        cls = Seq.module(object)
        seq = cls(args)
        return seq
    
    @staticmethod
    def create(t: Type[T], *args) -> "Seq[T]":
        """
        Create an untyped sequence from
        the given arguments
        """
        cls = Seq.module(t)
        seq = cls(args)
        return seq
    
    @classmethod
    def parse(cls, arg):
        """ 
        Parse the given value as an instance of
        this class
        """
        if isinstance(arg, cls):
            return arg
        return cls(arg)


    @property
    def count(self):
        return len(self.data)
    
    def __iadd__(self, other):
        self.add(other)

    def __add__(self, other):
        return self.__class__(self, other)

    def __iter__(self):
        return iter(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]

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
        match self.count:
            case 0:
                return f"0 {self.type.__name__}s"
            case 1:
                return f"1 {self.type.__name__}"
            case n:
                return f"{n} {self.type.__name__}s"

    def __repr__(self):
        return f"{self!s}"

def seq(type: Type[T], *args) -> Seq[T]:
    """
    Create a sequence of the given type
    from the given arguments
    """
    seq = Seq.create(type, args)
    return seq