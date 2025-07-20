import datetime as dt
import json
from attrs import define
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Type,
    TypeVar,
    Union,
    get_origin,
    Generic,
    Literal,
    LiteralString,
    Dict
)
from itertools import zip_longest
from uuid import UUID, uuid4
import pendulum as pn
from pendulum import datetime, duration, now
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.duration import Duration
from pendulum.interval import Interval
from pendulum.tz.timezone import UTC
from attrs import define, field
from cattrs.preconf.json import make_converter
import altair as alt



T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E", bound=Enum)


def to_int(value: Any = None) -> int:
    if isinstance(value, int):
        return value
    elif value is None:
        return 0
    else:
        return int(value)


def to_bool(value: Any = None) -> bool:
    if isinstance(value, bool):
        return value
    else:
        return bool(value)


def to_tick(value: Any = None) -> str:
    if value:
        return "✔️"
    else:
        return "❌"


def to_float(value: Any = None) -> float:
    if isinstance(value, float):
        return value
    elif value is None:
        return 0.0
    else:
        return float(value)


def to_string(value: Any = None) -> str:
    if isinstance(value, str):
        return value
    elif value is None:
        return ""
    else:
        return str(value)


def to_duration(*args, **kwargs) -> Duration:
    """
    Create a Duration from the given arguments
    """

    if not args:
        if kwargs:
            return duration(**kwargs)
        else:
            return duration()

    arg = args[0]

    if isinstance(arg, Interval):
        return arg.as_interval()

    elif isinstance(arg, Duration):
        return arg

    elif isinstance(arg, dt.timedelta):
        return pn.duration(seconds=arg.total_seconds())

    elif not arg:
        return duration()

    elif isinstance(arg, dict):
        return pn.duration(**arg)

    else:
        raise ValueError(
            f"Could not parse a Duration value from args {args} and kwargs {kwargs}"
        )


def to_elapsed(obj: Any) -> str:
    """
    Convert the given duration to
    a human readable string

    to_elapsed(dur(seconds=70)) == "1m 10s"
    """

    from functools import partial

    dur = to_duration(obj)
    micros, _ = divmod(dur.total_seconds() * 1000000, 1)
    micros = int(micros)
    millis, rem_micros = divmod(micros, 1000)
    seconds, rem_millis = divmod(millis, 1000)
    minutes, rem_secs = divmod(seconds, 60)
    hours, rem_mins = divmod(minutes, 60)
    days, rem_hours = divmod(hours, 24)

    def fmt_int(n: int, single, multi, none=""):
        """Format int"""
        if n == 0:
            return none
        elif n == 1:
            return f"{1}{single}"
        else:
            return f"{n}{multi}"

    fmt_day = partial(fmt_int, single="d", multi="d")
    fmt_hr = partial(fmt_int, single="h", multi="h")
    fmt_min = partial(fmt_int, single="m", multi="m")
    fmt_sec = partial(fmt_int, single="s", multi="s")

    ret = ""

    if days:
        ret = f"{fmt_day(days)} {fmt_hr(rem_hours)}"

    elif hours:
        ret = f"{fmt_hr(hours)} {fmt_min(rem_mins)}"

    elif minutes:
        ret = f"{fmt_min(minutes)} {fmt_sec(rem_secs)}"

    elif seconds:
        ret = f"{dur.total_seconds():.1f}s"

    elif millis:
        ret = f"{millis}ms"

    elif micros:
        ret = f"{micros}μs"

    else:
        ret = "0s"

    return ret


def to_datetime(value=None, timezone=UTC) -> DateTime:
    """
    Convert the given value to a pendulum datetime
    """

    if isinstance(value, DateTime):
        val = value

    elif isinstance(value, dt.datetime):
        val = pn.instance(value)

    elif isinstance(value, dt.date):
        val = datetime(year=value.year, month=value.month, day=value.day, tz=timezone)

    elif isinstance(value, str):
        parsed = pn.parser.parse(value)
        val = to_datetime(parsed, timezone=timezone)

    elif value is None:
        val = DateTime.min

    else:
        raise ValueError(f"Could not convert {value} of type {type(value)} to DateTime")

    localized = val.in_tz(timezone)

    return localized


def to_date(value=None) -> Date:
    """Convert the given value to a Date"""

    if isinstance(value, Date):
        return value

    elif isinstance(value, dt.date):
        return pn.date(value.year, value.month, value.day)

    else:
        return to_datetime(value).date()


def to_interval(*args) -> Interval:
    """
    Convert the given arguments to a time period
    """

    if not args:
        t = to_datetime()
        return Interval(t, t)

    n = len(args)
    if n == 1:
        arg = args[0]
        if isinstance(arg, Interval):
            return arg
        t = to_datetime(args[0])
        return Interval(t, t)

    a, b = args
    t0 = to_datetime(a)
    if isinstance(b, Duration):
        t1 = t0 + b
    else:
        t1 = to_datetime(b)

    return Interval(t0, t1, absolute=True)


def time_since(t: DateTime) -> Interval:
    return to_interval(t, now())


def elapsed_since(t: DateTime) -> str:
    return to_elapsed(time_since(t))


def to_minutes(x) -> float:
    """Convert the argument to minutes"""
    return to_duration(x).total_seconds() / 60.0


def middle_time(x) -> DateTime:
    """Get the middle time of a time period"""
    p = to_interval(x)
    return p.start.add(seconds=p.total_seconds() / 2)


def to_int_minutes(x):
    """Convert the argument to integer minutes"""
    return int(to_minutes(x))


def to_path(value: Union[Path, str], existing=False, is_file=True) -> Path:
    if isinstance(value, Path):
        path = value
    else:
        path = Path(value)

    if (path is None) or (existing and not path.exists()):
        raise FileNotFoundError(f"No file was found at {value}")

    elif is_file and existing and not path.is_file():
        raise ValueError(f"Path {value} was not a File.")

    elif not is_file and existing and not path.is_dir():
        raise ValueError(f"Path {value} was not a Directory.")

    else:
        return path


def to_filename(s):
    import string

    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = "".join(c for c in s if c in valid_chars)
    filename = filename.replace(" ", "_")  # I don't like spaces in filenames.
    return filename


def to_filepath(value: Union[Path, str], existing=False) -> Path:
    return to_path(value, existing=existing, is_file=True)


def to_existing_filepath(value) -> Path:
    return to_filepath(value, existing=True)


def to_id(value: Any = None) -> UUID:
    if isinstance(value, UUID):
        return value
    elif isinstance(value, str):
        return UUID(value)
    elif isinstance(x := getattr(value, "id", None), UUID):
        return x
    else:
        raise TypeError(f"Expected a UUID, got a {value}")


def read_json(path) -> dict:
    """Read JSON file as dict"""
    path = to_existing_filepath(path)
    text = path.read_text()
    data = json.loads(text)
    return data


def write_json(data, path, **kwargs):
    path_ = to_filepath(path)
    with path_.open("w") as f:
        json.dump(data, f, **kwargs)


def read_text(path) -> str:
    """Read file as text"""
    path = to_existing_filepath(path)
    text = path.read_text()
    return text


def to_directory(value: Union[Path, str], existing=True, create=False):
    path = to_path(value, existing=existing, is_file=False)
    if create and not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def round_minutes(dt: DateTime, precision: int = 1, up=False) -> DateTime:
    """Round the timestamp to the given precision (in minutes)"""
    new_minute = (dt.minute // precision + int(up)) * precision
    return dt.add(minutes=new_minute - dt.minute).replace(second=0)


def enumerate1(x):
    for i, y in enumerate(x):
        yield i + 1, y


def range1(x):
    return range(1, x + 1)


_enum_parsers_ = {}


def to_enum(ty: Type[E]) -> Callable[[Any], E]:
    if ty in _enum_parsers_:
        return _enum_parsers_[ty]

    def parse(v: Any) -> E:
        # Already the right type
        if isinstance(v, ty):
            return v
        # Lookup by name
        try:
            return ty[v]
        # Lookup by value
        except KeyError:
            return ty(v)

    _enum_parsers_[ty] = parse
    return parse


def flatten(*args):
    """
    Flatten the given arguments by yielding individual
    elements
    """

    def items(arg):
        if hasattr(arg, "items"):
            yield from items(arg.items)
        elif hasattr(arg, "__iter__"):
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

    optional: bool = False
    type : Type[T]
    
    def __init__(self, t: Type[T], *args):
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
            elif self.optional and item is None:
                yield item
            else:
                raise TypeError(
                    f"Could not add {item} of type {type(item)} to sequence of type {self.type}"
                )

    def add(self, *args):
        """Add to this list, a mutable operation"""
        for item in self.yield_from(args):
            self.data.append(item)
        return self

    def filter(self, f: Callable[[T], bool]) -> "Seq[T]":
        """Filter the sequence with the given function"""
        self.__class__(type, filter(f, self))
        return self

    def map(self, f: Callable[[T], U], type: Type[U] = object) -> "Seq[U]":
        """Map the given function of the sequence"""
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
            for a, b in zip_longest(self, other):
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


K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")
A = TypeVar("A", bound=LiteralString)
Id = Literal["id"]


class Map(Generic[K, V, A]):
    """
    A mapping from keys to values where the key
    exists as a field stored on the value (eg: item.id)
    """

    key_type: Type[K]
    val_type: Type[V]
    key_field: A
    data: Dict[K, V]

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
            elif hasattr(arg, "__iter__"):
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
                yield self.get_key(arg)  # type:ignore
            elif hasattr(arg, "__iter__"):
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
        """Add to this list, a mutable operation"""
        for val in self.gen_values(args):
            key = self.get_key(val)
            self.data[key] = val
        return self

    def filter(self, f: Callable[[V], bool]) -> "Map[K, V, A]":
        """Filter the sequence with the given function"""
        map = self.create(filter(f, self.vals))
        return map

    def to_dict(self, f: Callable[[V], U] = id) -> "Dict[K, U]":
        """Convert to a dictionary"""
        dict = {k: f(v) for k, v in self.data.items()}
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
        return self.create(self, other)

    def __iter__(self):
        return iter(self.data.values())

    def __len__(self):
        return len(self.data)

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        try:
            for a, b in zip_longest(self, other):
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


def id_map(v: Type[V], *args) -> Map[UUID, V, Id]:
    return Map(UUID, v, "id", *args)


def save_chart(chart: alt.Chart, path: Path, **properties) -> Path:
    """
    Save the given chart to the path, applying all
    properties given
    """
    chart = chart.properties(**properties)
    chart.save(path)
    return path


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


def map_field(
    key_type: Type[K], val_type: Type[V], key_field: A, **kwargs
) -> Map[K, V, A]:
    def factory():
        return Map(key_type, val_type, key_field)

    empty = factory()

    def convert(obj):
        return empty.parse(obj)

    return field(factory=factory, converter=convert, **kwargs)


def dict_field(**kwargs):
    return field(factory=dict, **kwargs)


def enum_field(default: E, **kwargs) -> E:
    return field(default=default, converter=to_enum(default.__class__), **kwargs)


def duration_field(default=None) -> Duration:
    defaultValue = to_duration(default)
    return field(default=defaultValue, converter=to_duration)


def datetime_field() -> DateTime:
    return field(factory=to_datetime, converter=to_datetime)


def date_field() -> Date:
    return field(factory=to_date, converter=to_date)


def period_field() -> Interval:
    return field(factory=to_interval, converter=to_interval)


def optional(f, **kwargs):
    default = kwargs.pop("default", f._default)

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
        t: Type = cls.__args__[0]  # type:ignore

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
        type_args = cls.__args__  # type:ignore
        key_type = type_args[0]
        val_type = type_args[1]
        key_field = type_args[2].__args__[0]

        def f(payload: dict, cls: Type[Map]):
            map = cls(key_type, val_type, key_field)
            for k, v in payload.items():
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
        print(
            f'write "{type(self).__name__}" -> {path} completed in {elapsed_since(t0)}'
        )
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
        model = json_converter.loads(string, cls)
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


__all__ = [
    T,
    U,
    E,
    to_bool,
    to_date,
    to_datetime,
    to_directory,
    to_duration,
    to_elapsed,
    to_enum,
    to_existing_filepath,
    to_filename,
    to_filepath,
    to_float,
    to_id,
    to_int_minutes,
    to_interval,
    to_minutes,
    to_path,
    to_string,
    Seq,
    lst,
    flatten,
    Map,
    enumerate1,
    range1,
    save_chart,
    BaseModel,
    seq_field,
    int_field,
    bool_field,
    field,
    map_field,
    id_field,
    str_field,
    float_field,
    enum_field,
    UUID,
    Id
]
