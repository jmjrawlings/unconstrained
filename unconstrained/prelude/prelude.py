import datetime as dt
import json
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar, Union, Callable

import pandas as pd
import pendulum as pn
from loguru import logger as log
from pendulum import date, datetime, duration, now, period, today
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.duration import Duration
from pendulum.period import Period
from pendulum.tz.timezone import UTC, Timezone
from rich import print
from rich.logging import RichHandler
from typing import Type, List, Set

DF = pd.DataFrame
T = TypeVar("T")
E = TypeVar("E", bound=Enum)


log.remove()

log.add(
    RichHandler(
        markup=True,
        rich_tracebacks=True,
        show_path=True,
        log_time_format='[%X]',
        enable_link_path=True,
        omit_repeated_times=False
    ),
    format='{message}'
    )

def to_int(value: Any = None) -> int:
    if value is None:
        return 0
    return int(value)


def to_bool(value: Any = None) -> bool:
    if value is None:
        return False
    return bool(value)


def to_tick(value: Any = None) -> str:
    if value:
        return "✔️"
    else:
        return "❌"


def to_float(value: Any = None) -> float:
    if value is None:
        return 0.0
    return float(value)


def to_string(value: Any = None) -> str:
    if value is None:
        return ""
    return str(value)


def to_case_insensitive(x) -> str:
    if x is None:
        return ""
    else:
        x = str(x)
        return x.replace(" ", "").lower()


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

    if isinstance(arg, Period):
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
    micros, _           = divmod(dur.total_seconds() * 1000000, 1)
    micros = int(micros)
    millis, rem_micros  = divmod(micros, 1000)
    seconds, rem_millis = divmod(millis, 1000)
    minutes, rem_secs   = divmod(seconds, 60)
    hours, rem_mins     = divmod(minutes, 60)
    days, rem_hours     = divmod(hours, 24)

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
        val = datetime(
            year=value.year, 
            month=value.month,
            day=value.day,
            tz=timezone
        )

    elif isinstance(value, str):
        parsed = pn.parser.parse(value)
        val = to_datetime(parsed, timezone=timezone)

    elif value is None:
        val = DateTime.min

    else:
        raise ValueError(f"Could not convert {value} of type {type(value)} to DateTime")

    localized = val.in_tz(timezone)
    
    return localized


def to_date(value = None) -> Date:
    """Convert the given value to a Date"""

    if isinstance(value, Date):
        return value

    elif isinstance(value, dt.date):
        return pn.date(value.year, value.month, value.day)

    else:
        return to_datetime(value).date()


def to_period(*args) -> Period:
    """
    Convert the given arguments to a time period
    """
                    
    if not args:
        t = to_datetime()
        return period(t, t)

    n = len(args)
    if n == 1:
        arg = args[0]
        if isinstance(arg, Period):
            return arg
        t = to_datetime(args[0])
        return period(t, t)

    a, b = args
    t0 = to_datetime(a)
    if isinstance(b, Duration):
        t1 = t0 + b
    else:
        t1 = to_datetime(b)

    return Period(t0, t1, absolute=True)



def time_since(t: DateTime) -> Period:
    return to_period(t, now())


def elapsed_since(t: DateTime) -> str:
    return to_elapsed(time_since(t))


def to_minutes(x) -> float:
    """Convert the argument to minutes"""
    return to_duration(x).total_seconds() / 60.0


def middle_time(x) -> DateTime:
    """Get the middle time of a time period"""
    p = to_period(x)
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
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ','_') # I don't like spaces in filenames.
    return filename


def to_filepath(value: Union[Path, str], existing=False) -> Path:
    return to_path(value, existing=existing, is_file=True)


def to_existing_filepath(value) -> Path:
    return to_filepath(value, existing=True)


def read_json(path) -> dict:
    """ Read JSON file as dict """
    path = to_existing_filepath(path)
    text = path.read_text()
    data = json.loads(text)
    return data


def write_json(data, path, **kwargs):
    path_ = to_filepath(path)
    with path_.open("w") as f:
        json.dump(data, f, **kwargs)


def read_text(path) -> str:
    """ Read file as text """
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
    for i,y in enumerate(x):
        yield i+1, y


def range1(x):
    return range(1, x+1)

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


_set_parsers_ = {}

def to_typed_set(ty: Type[T]) -> Callable[..., T]: 
    
    if ty in _set_parsers_:
        return _set_parsers_[ty]
    
    def parse(*args) -> Set[T]:
                                                                            
        def unpack(arg):
            # Correct type
            if isinstance(arg, ty):
                yield arg
            # Iterable
            elif hasattr(arg, '__iter__'):
                for a in arg:
                    yield unpack(a)
            # Callable                
            elif callable(arg):
                yield unpack(arg())
            # Typecheck                
            else:
                raise ValueError(f"{arg} was not of type {ty}")

        result = set(unpack(*args))
        return result

    _set_parsers_[ty] = parse
    return parse #type:ignore
