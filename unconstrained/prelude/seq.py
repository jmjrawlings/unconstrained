from .prelude import *
from typing import Generic, Any
from itertools import zip_longest

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
            
    def __init__(self, t: Type[T],  *args):
        self.type = t
        self.data = []
        for item in self.yield_from(args):
            self.data.append(item)

    def get(self, idx: int) -> T:
        return self.data[idx]

    def yield_from(self, args):
        for item in flatten(args):
            if isinstance(item, self.type):
                yield item
            elif (self.optional and item is None):
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
        self.__class__(type, filter(f, self))
        return self
    
    def map(self, f: Callable[[T],U], type: Type[U] = object) -> "Seq[U]":
        """ Map the given function of the sequence """
        seq = self.__class__(type, (f(x) for x in self))
        return seq
    
    def create(self: "Seq[T]", *args) -> "Seq[T]":
        return self.__class__(self.type, *args)    
        
    def copy(self):
        seq = self.__class__(self.type)
        seq.data = self.data.copy()
        return seq

    def parse(self, obj) -> "Seq[T]":
        if isinstance(obj, self.__class__):
            if obj.type == self.type:
                return obj
        return self.create(obj)

    @property
    def count(self):
        return len(self.data)
    
    def __iadd__(self, other):
        self.add(other)

    def __add__(self, other):
        return self.__class__(self.type, self, other)

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

def lst(*args) -> Seq[Any]:
    """
    Create a sequence of the given type
    from the given arguments
    """
    seq = Seq(object, args)
    return seq