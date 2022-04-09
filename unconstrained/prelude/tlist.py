from .prelude import *
from typing import Generic, TypeVar, Any, Dict, Type, Iterator, List as PyList, Tuple, Optional, Sequence, Iterable, Callable
from toolz import itertoolz as iz

T = TypeVar("T")
U = TypeVar("U")
L = TypeVar("L", bound="TList")


class TList(Generic[T]):
    val_type : Type[T] = None #type:ignore
                            
    def __init__(self, *args):
        self.list : List[T] = list()
        self.add(*args)
        

    def add(self, *args):
        """
        Add an element to this List
        """
                
        for arg in args:

            # Argument is of the correct type                                    
            if self.val_type: 
                if isinstance(arg, self.val_type):
                    self.list.append(arg)
                    continue

            # Untyped and string - handle here so dont recurse
            elif isinstance(arg, str):
                self.list.append(arg)
                continue

            # Try to recurse
            try:
                items = list(arg) #@IgnoreException
            except:
                items = []
                if self.val_type:
                    raise ValueError(f"Could not add {arg} of type {type(arg)} to {self!r}")
                else:
                    self.list.append(arg)

            for item in items:
                assert item != arg
                self.add(item)
                

    @property
    def count(self) -> int:
        """
        Number of elements in the map
        """
        return len(self)


    @property
    def first(self) -> T:
        """
        Get the first item
        """
        return self.list[0]


    @property
    def try_first(self) -> Optional[T]:
        """
        Get the first item - return None if the Map is empty
        """
        if not self:
            return None
        return self.first


    @property
    def last(self) -> T:
        """Get the last item"""
        return self.list[-1]


    @property
    def try_last(self) -> Optional[T]:
        if not self:
            return None
        return self.last


    def enumerate(self) -> Iterable[Tuple[int, T]]:
        """
        Index/Value pairs starting at 0
        """                
        return enumerate(self)


    def enumerate1(self) -> Iterable[Tuple[int, T]]:
        """
        Index/Value pairs starting at 1
        """                
        for i, v in self.enumerate():
            yield i + 1, v


    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse=False):
        self.list.sort(key=key, reverse=reverse)
        return self


    def to_set(self):
        return set(self.list)


    def sorted(self, key: Optional[Callable[[T], Any]] = None, reverse=False):
        values = sorted(self.list, key=key, reverse=reverse)
        new = self.make(*values)
        return new


    def groupby(self, f) -> Dict[T, U]:
        result = {}
        for key, values in iz.groupby(f, self.list).items():
            result[key] = self.make(values)

        return result


    @classmethod
    def make(cls, *args):
        return cls(*args)


    def partition(self, key) -> Tuple[List[T], List[T]]:
        inside = self.filter(key)
        outside = self.filter(lambda v: v not in inside)
        return inside, outside


    def sum(self, key = None, default=0):
        if key:
            return self.map(key).sum()
        else:
            return sum(self.list, start=default)


    def max(self, key = None, default=0):
        if key:
            return self.map(key).max()
        else:
            return max(self.list, default=default)

    def min(self, key = None, default=0):
        if key:
            return self.map(key).min()
        else:
            return min(self.list, default=default)

    def clear(self):
        self.list.clear()
        return self


    def take(self, n : int):
        return self.make(self.list[:n])


    def __getitem__(self, key) -> T:
        return self.list[key]


    def filter(self, f) -> "TList[T]":
        filtered = self.make()
                
        for arg in self:
            if f(arg):
                filtered.add(arg)

        return filtered


    def map(self, f_ = None):
        if not f_:
            return to_list(self)

        if isinstance(f_, str):
            name = f_
            f = lambda x: getattr(x, name)
        else:
            f = f_

        return to_list([f(x) for x in self])
        

    def copy(self):
        """
        Create a new collection that contains
        the same elements
        """

        return self.make(self)


    def pairwise(self):
        """
        Return the values in pairs
        """
        values = self.list
        pairs = zip(values[:-1], values[1:])
        return pairs


    def __add__(self, other):
        """
        Create a new Map by combining
        this and the other
        """
        return self.make(self, other)


    def __iadd__(self, other):
        """
        Create a new Map by combining
        this and the other
        """
        self.add(other)
       

    def __contains__(self, obj) -> bool:
        return obj in self.list


    def __iter__(self) -> Iterator[T]:
        return iter(self.list)


    def __len__(self):
        return len(self.list)


    def __bool__(self):
        return bool(self.list)


    def __eq__(self, other) -> bool:
        try:
            for a,b in zip(self, other): #@IgnoreException
                if a != b:
                    return False
            return True
        except:
            return False


    def __repr__(self):
        return f"<{self!s}>"


    def __str__(self):
        if self.val_type:
            return f"List of {self.count} {self.val_type.__name__}"
        else:
            return f"List of {self.count} items"
        


def make_list_class(cls : Type[T]) -> Type[TList[T]]:
    class Lst(TList):
        val_type = cls

    return Lst


def to_list(*args, type=None):
    list_class = make_list_class(type)
    list = list_class(*args)    
    return list


def list_field(cls : Type[T], **kwargs) -> TList[T]:
    list_class = make_list_class(cls)
    return make_field(list_class, list_class(), list_class, **kwargs)
    
