from .prelude import *
from typing import Generic, TypeVar, Any, Dict, Type, Iterator, List, Tuple, Optional, Sequence, Iterable, Callable
import itertools as iz
from .tlist import make_list_class, to_list, TList

K = TypeVar("K")
V = TypeVar("V")
D = TypeVar("D", bound="Map")


class Map(Generic[K, V]):
    """
    A mapping from keys to values.

    This is a key data structure that
    gets used everywhere.

    The idea is keeping track of a collection
    of values of the same type.  These values
    must store their key as a member/field.

    Given that you have a Map, there are many
    powerful operations you can do on it.

    Dict like operations
    - map.get
    - map.try_get
    - map.update
    - map.remove
    - map.add

    Set like operations
    - map.filter
    - map.union
    - map.subset
    - map.superset
    - map.difference

    """

    
    key_type : Type[K] = str    #type:ignore
    val_type : Type[V] = object #type:ignore
    

    def __init__(self, *args) -> None:
        self.dict: Dict[K, V] = dict()
        self.add(*args)


    @classmethod
    def get_key(cls, obj):
        return obj.get_id()


    @classmethod
    def parse(cls: Type[D], obj: Any = None) -> D:  # type:ignore
        """
        Parse the given value as a Map
        """

        if isinstance(obj, cls):
            return obj

        return cls.create(obj)


    @classmethod
    def parse_key(cls, obj: Any) -> K:
        """
        Parse the given object as a 
        Key to this Map
        """
        if obj is None:
            return None

        if isinstance(obj, cls.key_type):
            return obj

        return cls.get_key(obj)


    def sort_by_keys(self, cmp=str):
        """
        Sort the internal dictionary by keys
        """
        self.dict = {k: self.dict[k] for k in sorted(self.dict.keys(), key=cmp)}


    @classmethod
    def create(cls: Type[D], *args) -> D:
        return cls(*args)


    def add_unique(self, *args):
        """
        Add elements to the Map, will throw
        an exception if they already exist
        """
        return self.add(*args, overwrite=False)


    def add(self: D, *args, overwrite=True, warn=False):
        """
        Add an element to this Map - ensuring that
        the item is only added if it matches the 
        `val_type` of this list.
        
        If the argument given is not of the correct type,
        attempt to iterate over it recursively.
        
        """
        
        for arg in args:

            if isinstance(arg, self.val_type):
                key = self.parse_key(arg)
                old = self.dict.get(key)

                if old is not None:
                    if not overwrite:
                        raise Exception(
                            f"Could not add {key} = {arg} to collection as it would overwrite {old}"
                        )
                    if warn:
                        log.warning(f"Overwriting {key} = {old} with {arg}")

                self.dict[key] = arg

            elif isinstance(arg, dict):
                for val in arg.values():
                    self.add(val, overwrite=overwrite, warn=warn)

            else:
                try:
                    items = list(arg)
                except TypeError:
                    raise Exception(f'Could add arg {arg} of type {type(arg)} to {self!r}')
                for val in items:
                    self.add(val, overwrite=overwrite, warn=warn)


    def remove(self: D, *args) -> D:
        for arg in args:
            if isinstance(arg, self.val_type):
                key = self.parse_key(arg)
                self.dict.pop(key)

            elif isinstance(arg, self.key_type):
                self.dict.pop(arg)

            elif isinstance(arg, dict):
                for arg_ in arg.keys():
                    self.remove(arg_)
            else:
                for arg_ in arg:
                    self.remove(arg_)

    @property
    def count(self) -> int:
        """
        Number of elements in the map
        """
        return len(self)

    @property
    def keys(self) -> List[K]:
        """
        Return the keys as a list
        """
        return list(self.dict.keys())

    @property
    def values(self) -> List[V]:
        """
        Return the keys as a list
        """
        return self.to_list()
        

    def to_list(self) -> List[V]:
        return to_list(self)


    @property
    def items(self) -> List[Tuple[K, V]]:
        """
        Return the key/value tuples as a list
        """
        return list(self.dict.items())


    @property
    def first(self) -> V:
        """
        Get the first item
        """
        return iz.first(self.dict.values())


    @property
    def try_first(self) -> Optional[V]:
        """
        Get the first item - return None if the Map is empty
        """
        if not self:
            return None
        return self.first


    @property
    def last(self) -> V:
        """Get the last item"""
        return iz.last(self.dict.values())


    @property
    def try_last(self) -> Optional[V]:
        if not self:
            return None
        return self.last


    def enumerate(self) -> Iterable[Tuple[int, V]]:
        """
        Index/Value pairs starting at 0
        """                
        return enumerate(self)


    def enumerate1(self) -> Iterable[Tuple[int, V]]:
        """
        Index/Value pairs starting at 1
        """                
        for i, v in self.enumerate():
            yield i + 1, v


    def union(self, *obj):
        """
        Create a new collection that
        only contains elements in both the
        others
        """
        coll = self.create()
        other = self.create(*obj)
        for val in other:
            if val in self:
                coll.add(val)
        return coll


    def difference(self, obj):
        """
        Create a new collection that
        only items in the first that
        do not appear in the second
        """
        return self - obj


    def subset(self, *obj) -> bool:
        """
        Is this a subset of the other?
        """
        other = self.create(*obj)
        for val in self:
            if val not in other:
                return False

        return True


    def superset(self, *obj) -> bool:
        """
        Is this a superset of the other
        """
        other = self.create(*obj)
        return other.subset(self)


    def disjoint(self, *other) -> bool:
        return not self.union(*other)


    def intersects(self, *other) -> bool:
        return bool(self.union(*other))


    def sort(self: D, key: Optional[Callable[[V], Any]] = None, reverse=False) -> D:
        values = self.to_list()
        if key is None:
            values = sorted(values, reverse=reverse)
        else:
            values = sorted(values, key=key, reverse=reverse)

        return self.create(values)


    def groupby(self: D, f_) -> Dict[T, D]:

        if isinstance(f_, str):
            f = lambda x: getattr(x, f_)
        else:
            f = f_

        result = {}
        for key, values in iz.groupby(f, self.to_list()).items():
            result[key] = self.create(values)

        return result


    def partition(self: D, key) -> Tuple[D, D]:
        inside = self.filter(key)
        outside = self.filter(lambda v: v not in inside)
        return inside, outside


    def clear(self: D) -> D:
        self.dict.clear()
        return self


    def take(self: D, n: Optional[int]) -> D:
        if n is None:
            return self
        return self.create(self.to_list()[:n])


    def get(self, key) -> V:
        """
        Get the item associated with the given Key

        Throws a KeyError if not present - use
        `try_get` for safe access
        """
        val = self.try_get(key)
        if val is None:
            msg = f'"{key}" could not be found in "{self!s}"'
            raise KeyError(msg)
        return val


    def __getitem__(self, key) -> V:
        return self.get(key)        


    def try_get(self, key) -> Optional[V]:
        key = self.parse_key(key)
        val = self.dict.get(key)
        return val

    def update(self: D, other: "Map[K,V]") -> D:
        """Update this with the other"""
        for key, val in other.items:
            self.dict[key] = val

        return self

    def filter(self: D, *args) -> D:
        """
        Returned a new Map with elements
        that match the given filters:

        A filter can be:
            - A callable
            - A key
            - A value
            - Any combination thereof

        """
        map = self.create()
        list = to_list(*args)
        
        for arg in list:
            if callable(f := arg):
                for item in self:
                    if f(item):
                        map.add(item)
            else:
                item = self.get(arg)
                map.add(item)

        return map


    def map(self, f_):
        """
        Return a dictionary with the elements transformed
        with the given function
        """
        if isinstance(f_, str):
            name = f_
            f = lambda x: getattr(x, name)
        else:
            f = f_

        return {k: f(v) for k, v in self.dict.items()}


    def copy(self: D) -> D:
        """
        Create a new collection that contains
        the same elements
        """

        return self.create(self)


    def pairwise(self: D):
        """
        Return the values in pairs
        """
        values = self.to_list()
        pairs = zip(values[:-1], values[1:])
        return pairs


    def sum(self, *args, **kwargs):
        return self.to_list().sum(*args, **kwargs)        


    def max(self, *args, **kwargs):
        return self.to_list().max(*args, **kwargs)        


    def min(self, *args, **kwargs):
        return self.to_list().min(*args, **kwargs)        


    def __iadd__(self: D, other) -> D:
        """
        Allow addition syntax for adding elements

        map += Item()
        """

        self.add(other)
        return self


    def __add__(self: D, other) -> D:
        """
        Create a new Map by combining
        this and the other
        """

        new = self.create()
        new.add(self)
        new.add(other)
        return new


    def __sub__(self: D, other) -> D:
        """
        Create a new Map by removing
        the other form this one
        """
        new = self.copy()
        new.remove(other)
        return new


    def __isub__(self: D, other) -> D:
        """
        Allow subtraction syntax for
        removing elements

        map -= item
        """

        self.remove(other)
        return self


    def __contains__(self, obj) -> bool:
        key = self.parse_key(obj)
        inside = key in self.dict
        return inside


    def __iter__(self) -> Iterator[V]:
        return iter(self.dict.values())


    def __len__(self):
        return len(self.dict)


    def __bool__(self):
        return bool(self.dict)


    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Map):
            return False
        k1 = self.keyset
        k2 = o.keyset
        return k1 == k2


    def __repr__(self):
        return f"<{self}>"


    def __str__(self):
        return f"{self.count} {self.val_type.__name__}s"


class FixedMap(Map[K, V]):
    """
    A map where all of the
    possible element are known
    at compile time
    """

    map_type: Type[Map[K, V]]

    def __init__(self):
        """
        Add all of the static
        members
        """
        super().__init__()

        for val in vars(type(self)).values():
            if isinstance(val, self.val_type):
                self.add_unique(val)

    @classmethod
    def parse_key(self, obj: V) -> K:
        return self.map_type.parse_key(obj)

    def parse(self, *args):
        return self.create(args)

    def create(self, *args) -> Map[K, V]:
        """
        Create a map that can only contain
        members of this fixed set
        """

        map = self.map_type.create()

        def add(arg):
            if arg is None:
                return
            elif isinstance(arg, map.key_type):
                val = self.get(arg)
                map.add(val)
            elif isinstance(arg, map.val_type):
                val = arg
                map.add(val)
            elif callable(arg):
                add(arg())
            else:
                for x in arg:
                    add(x)

        for arg in args:
            add(arg)

        return map


def map_field(cls: Type[T], **kwargs) -> T:
    return attr.ib(
        factory=cls.create,
        converter=cls.parse,
        **kwargs
    )


# def deserialize_map(obj: Map):
#     vals = obj.list
#     x = converter.unstructure(vals)
#     return x


# def serialize_map(dicts, type : Type[Map]):
#     objs = [converter.structure(dict, type.val_type) for dict in dicts]
#     map = type.create(objs)
#     return map


# # converter.register_structure_hook(Map, serialize_map)
# # converter.register_unstructure_hook(Map, deserialize_map)
