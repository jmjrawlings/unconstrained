from ..prelude import *
from ..model import *
from typing import AsyncIterable, Tuple, List, Optional, Dict
from datetime import timedelta
from minizinc import Method
from minizinc import Result as MzResult
from minizinc import Solver as Solver
from minizinc import Status as MzStatus
from minizinc import Instance
from minizinc import Driver
from typing import TypedDict
from shutil import copy
from attrs import field, define
import math
import logging

logging.basicConfig(level=logging.DEBUG)


class Statistics(TypedDict, total=False):
    # Number of search nodes
    nodes: int
    # Number of leaf nodes that were failed
    failures: int
    # Number of times the solver restarted the search
    restarts: int
    # Number of variables
    variables: int
    # Number of integer variables created by the solver
    intVariables: int
    # Number of Boolean variables created by the solver
    boolVariables: int
    # Number of floating point variables created by the solver
    floatVariables: int
    # Number of set variables created by the solver
    setVariables: int
    # Number of propagators created by the solver
    propagators: int
    # Number of propagator invocations
    propagations: int
    # Peak depth of search tree
    peakDepth: int
    # Number of nogoods created
    nogoods: int
    # Number of backjumps
    backjumps: int
    # Peak memory (in Mbytes)
    peakMem: float
    # Initialisation time
    initTime: timedelta
    # Solving time
    solveTime: timedelta
    # Flattening time
    flatTime: timedelta
    # Number of paths generated
    paths: int
    # Number of Boolean variables in the flat model
    flatBoolVars: int
    # Number of floating point variables in the flat model
    flatFloatVars: int
    # Number of integer variables in the flat model
    flatIntVars: int
    # Number of set variables in the flat model
    flatSetVars: int
    # Number of Boolean constraints in the flat model
    flatBoolConstraints: int
    # Number of floating point constraints in the flat model
    flatFloatConstraints: int
    # Number of integer constraints in the flat model
    flatIntConstraints: int
    # Number of set constraints in the flat model
    flatSetConstraints: int
    # Optimisation method in the Flat Model
    method: str
    # Number of reified constraints evaluated during flattening
    evaluatedReifiedConstraints: int
    # Number of half-reified constraints evaluated during flattening
    evaluatedHalfReifiedConstraints: int
    # Number of implications removed through chain compression
    eliminatedImplications: int
    # Number of linear constraints removed through chain compression
    eliminatedLinearConstraints: int


# Expose methods at top levl
MAXIMIZE = Method.MAXIMIZE
MINIMIZE = Method.MINIMIZE
SATISFY  = Method.SATISFY


# Expose supported solvers at top level
CHUFFED = 'chuffed'
ORTOOLS = 'or-tools'
GECODE  = 'gecode'
COINBC  = 'coin-bc'


def get_solver(x) -> Solver:
    """
    Get an installed solver from the
    given argument
    """
            
    if isinstance(x, Solver):
        return x

    solver = Solver.lookup(x)
    
    if not solver:
        raise ValueError(f'Could not parse solver from {x}')

    return solver


def get_driver() -> Driver:
    """
    Get the MiniZinc driver, throws an 
    exception if not found
    """
    driver = Driver.find()
    if driver is None:
        raise Exception(f'MiniZinc is not installed')
    return driver


def get_available_solvers() -> List[Solver]:
    """
    Get the available solvers
    """
    driver = get_driver()
    solvers = {}
    for tag, tag_solvers in driver.available_solvers(True).items():
        for solver in tag_solvers:
            solvers[solver.id] = solver

    solvers = list(solvers.values())
    for solver in solvers:
        log.info(f'MiniZinc Solver "{solver.name}" is installed')

    return solvers


class Status(Enum):
    FEASIBLE      = "feasible"
    OPTIMAL       = "optimal"
    THRESHOLD     = "threshold"
    UNSATISFIABLE = "unsatisfiable"
    TIMEOUT       = "timeout"
    ERROR         = "error"
    UNKNOWN       = "unknown"
    UNBOUNDED     = "unbounded"
    ALL_SOLUTIONS = "all_solutions"
        
    @property
    def has_solution(self):
        return self in [Status.FEASIBLE, Status.OPTIMAL, Status.THRESHOLD]

    @property
    def is_error(self):        
        return self in [Status.ERROR, Status.UNKNOWN, Status.UNBOUNDED]


class VariableChoice(Enum):
    # choose in order from the array
    INPUT_ORDER = "input_order"
    # choose the variable with the smallest domain size
    FIRST_FAIL = "first_fail"
    # choose the variable with the smallest value in its domain.
    SMALLEST = "smallest"
    # choose the variable with the smallest value of domain size divided by weighted degree, which is the number of times it has been in a constraint that caused failure earlier in the search
    DOM_W_DEG = "dom_w_deg"
    

class ConstrainChoice(Enum):
    # assign the variable its smallest domain value
    INDOMAIN_MIN = "indomain_min"
    # assign the variable its median domain value (or the smaller of the two middle values in case of an even number of elements in the domain)
    INDOMAIN_MED = "indomain_median"
    # assign the variable a random value from its domain
    INDOMAIN_RANDOM = "indomain_random"
    # bisect the variables domain excluding the upper half
    INDOMAIN_SPLIT = "indomain_split"


class FlattenOption(Enum):
    """
    Two-pass compilation means that the MiniZinc compiler will 
    first compile the model in order to collect some global 
    information about it, which it can then use in a second pass 
    to improve the resulting FlatZinc. 
    
    For some combinations of model and target solver,
    this can lead to substantial improvements in solving time.
    However, the additional time spent on the first compilation pass 
    does not always pay off.
    """

    # Do not optimiser flattening
    NONE = 0 
    # Single flattening step (default)
    SINGLE_PASS = 1 
    # Flatten twice to make better flattening decisions for the target
    TWO_PASS = 2 
    # Perform root-node-propagation with Gecode (adds –two-pass)
    USE_GECODE = 3 
    # Probe bounds of all variables at the root node (adds –use-gecode)
    SHAVE = 4 
    # Probe values of all variables at the root node (adds –use-gecode)
    SAC = 5 


# Expose solve status at top level
FEASIBLE      = Status.FEASIBLE
OPTIMAL       = Status.OPTIMAL
THRESHOLD     = Status.THRESHOLD
UNSATISFIABLE = Status.UNSATISFIABLE
TIMEOUT       = Status.TIMEOUT
ERROR         = Status.ERROR
UNKNOWN       = Status.UNKNOWN
UNBOUNDED     = Status.UNBOUNDED
ALL_SOLUTIONS = Status.ALL_SOLUTIONS


# Expose search variable choice at top level
INPUT_ORDER = VariableChoice.INPUT_ORDER
FIRST_FAIL  = VariableChoice.FIRST_FAIL
SMALLEST    = VariableChoice.SMALLEST
DOM_W_DEG   = VariableChoice.DOM_W_DEG


# Expose search variable choice at top level
INDOMAIN_MIN    = ConstrainChoice.INDOMAIN_MIN
INDOMAIN_MED    = ConstrainChoice.INDOMAIN_MED
INDOMAIN_RANDOM = ConstrainChoice.INDOMAIN_RANDOM
INDOMAIN_SPLIT  = ConstrainChoice.INDOMAIN_SPLIT


# Expose Flatten Options at top level
FLATTEN_NONE        = FlattenOption.NONE
FLATTEN_SINGLE_PASS = FlattenOption.SINGLE_PASS
FLATTEN_TWO_PASS    = FlattenOption.TWO_PASS
FLATTEN_USE_GECODE  = FlattenOption.USE_GECODE
FLATTEN_SHAVE       = FlattenOption.SHAVE
FLATTEN_SAC         = FlattenOption.SAC

@define
class Result(BaseModel):
    """
    The result of solving a model
    """
    name             : str             = string_field()
    model_string     : str             = string_field()
    model_file       : str             = string_field()
    data_string      : str             = string_field()
    data_file        : str             = string_field()
    method           : Method          = enum_field(Method.SATISFY)
    status           : Status          = enum_field(Status.FEASIBLE)
    error            : str             = string_field()
    flatten_time     : Duration        = duration_field()
    start_time       : DateTime        = datetime_field()
    end_time         : DateTime        = datetime_field()
    statistics       : Statistics      = field(factory=Statistics)
    iteration        : int             = int_field()
    objective        : Optional[int]   = None
    objective_bound  : Optional[int]   = None
    absolute_gap     : Optional[int]   = None
    relative_gap     : Optional[float] = None
    absolute_delta   : Optional[int]   = None
    relative_delta   : Optional[float] = None
    variables        : Dict[str, Any]  = dict_field()
        
    @property
    def solve_time(self) -> Period:
        return to_period(self.start_time, self.end_time)

    @property
    def solve_duration(self) -> Duration:
        return self.solve_time.as_interval()

    @property
    def elapsed(self):
        return to_elapsed(self.solve_time)

    @property
    def has_objective(self):
        return self.objective is not None

    @property
    def has_bound(self):
        return self.objective_bound is not None

    @property
    def has_solution(self):
        return self.status.has_solution

    def get_value(self, name, *indices) -> Any:
        """
        Get the solution value for the given name
        and indices

        result.get_value('a')
        result.get_value('an_array', 1)
        result.get_value('a_2d_array', 4, 10)
        """
        
        if name not in self.variables:
            raise KeyError(f'Solution does not contain a value for "{name}"')

        value = self.variables[name]
        for i in indices:
            value = value[i]

        return value

    def get_int(self, name, *indices) -> int:
        return self.get_value(name, *indices)

    def get_bool(self, name, *indices) -> bool:
        return self.get_value(name, *indices)
        
    def __getitem__(self, key):
        name = key[0]
        indices = key[1:]
        return self.get_value(name, *indices)

    def __str__(self):
        return f'{self.name} - {self.status.name}'

    def __repr__(self) -> str:
        return f'<{self!s}>'
    
@define
class SolveOptions(BaseModel):
    solver_id       : str           = string_field(default="gecode")
    threads         : int           = int_field(default=4)
    time_limit      : Duration      = duration_field(default=dict(minutes=1))
    flatten_options : FlattenOption = enum_field(FlattenOption.SINGLE_PASS)
    free_search     : bool          = bool_field(default=True)
    

async def solve(
        model : str,
        options : SolveOptions,
        name : str = 'model',
        debug_path : Union[Path, str] = '/tmp',
        parameters : Optional[Dict[str, Any]] = None,
        **kwargs
        ) -> AsyncIterable[Result]:

    """
    Solve the given minizinc model.
    """
    from copy import deepcopy
        
    solver = get_solver(options.solver_id)
    debug_path = to_directory(debug_path or '/tmp', create=True)
    
    # Initial solution
    result = Result(name=name, model_string=model)
        
    # Create the MiniZinc Instance
    try:
        instance = Instance(solver)
        instance.add_string(result.model_string)
                        
        for param, value in (parameters or {}).items():
            instance[param] = value
                                                                                                    
        with instance.files() as files:
            for file in files:

                debug_root = to_filename(name)
                debug_file = debug_path / f'{debug_root}_{file.name}'
                copy(file, debug_file)
                                
                if file.suffix == '.mzn':
                    result.model_string += file.read_text()
                    result.model_file = str(debug_file)
                    file_type = 'model'
                elif file.suffix == '.json':
                    result.data_string += file.read_text()
                    result.data_file = str(debug_file)
                    file_type = 'data'
                elif file.suffix == '.dzn':
                    result.data_string += file.read_text()
                    result.data_file = str(debug_file)
                    file_type = 'data'
                else:
                    file_type = "???"
                
                log.info(f'"{name}" {file_type} written to {debug_file}')


        result.method = instance.method
        result.status = Status.FEASIBLE
        variables = {key for key in (instance.output or {}).keys() if key != '_checker'}
        
    # Most likely syntax error
    except Exception as e:
        result.error = e.args[0]
        result.status = Status.ERROR
        instance = None
        variables = set()
        log.error(f'{type(e).__name__}: {result.error}')
                    
    if instance is None:
        yield result
        return
    
    previous = result
                        
    try:
        mz_result : MzResult
                        
        async for mz_result in instance.solutions(
            timeout = options.time_limit,
            optimisation_level = options.flatten_options.value,
            free_search = '-f' in solver.stdFlags and options.free_search,
            processes = '-p' in solver.stdFlags and options.threads,
            **kwargs
        ):
        
            statistics = previous.statistics.copy()
            statistics.update(mz_result.statistics) #type:ignore
                                                        
            result = Result(
                name            = name,
                iteration       = previous.iteration + 1,
                start_time      = previous.start_time,
                end_time        = now(),
                statistics      = statistics,
                flatten_time    = previous.flatten_time,
                method          = previous.method,
                model_string    = previous.model_string,
                model_file      = previous.model_file,
                status          = Status.FEASIBLE,
                variables       = deepcopy(previous.variables)
            )
                        
            if 'flatTime' in statistics:
                flat_time = statistics.pop('flatTime')
                result.flatten_time = to_duration(flat_time)
                                                                                               
            # No solution - MiniZinc has terminated
            if mz_result.solution is None:
                                                
                if mz_result.status == MzStatus.OPTIMAL_SOLUTION:
                    result.variables = previous.variables.copy()
                    result.objective = previous.objective
                    result.objective_bound = previous.objective
                    result.absolute_delta = previous.absolute_gap
                    result.relative_delta = previous.absolute_delta
                    result.absolute_gap = 0
                    result.relative_gap = 0.0
                    status = OPTIMAL

                elif mz_result.status == MzStatus.UNSATISFIABLE:
                    status = UNSATISFIABLE

                elif mz_result.status == MzStatus.SATISFIED:
                    status = FEASIBLE

                elif mz_result.status == MzStatus.UNBOUNDED:
                    status = UNBOUNDED

                elif mz_result.status == MzStatus.ALL_SOLUTIONS:
                    status = ALL_SOLUTIONS

                elif mz_result.status == MzStatus.UNKNOWN:
                    if result.solve_duration > options.time_limit:
                        status = TIMEOUT
                    else:
                        status = UNKNOWN

                else:
                    status = ERROR

                result.status = status
                
                for key,value in statistics.items():
                    log.debug(f'"{name}" {key} = {value}')

                log.log(
                    logging.INFO if status.has_solution else logging.ERROR,
                    f'"{name}" returned "{status.name}" after {result.elapsed}'
                )
                continue
            
            # An intermediate solution has been given
            objective : Optional[int]   = None
            bound     : Optional[int]   = None
            abs_gap   : Optional[int]   = None
            rel_gap   : Optional[float] = None
            abs_delta : Optional[int]   = None
            rel_delta : Optional[float] = None

            # Extract objective
            if (objective := mz_result.objective) is not None: # type:ignore
                result.objective = int(objective)
                objective = result.objective

            # Extract objective bound
            if (bound := statistics.pop('objectiveBound', None)) is not None: # type:ignore
                if math.isfinite(bound):
                    result.objective_bound = int(bound)
                    bound = result.objective_bound

            # Calculate absolute gap
            if (bound is not None and objective is not None):
                abs_gap = abs(objective - bound)

            # Calculate relative gap
            if (abs_gap is not None and bound):
                rel_gap = abs_gap / bound
                
            # Calculate absolute delta                    
            if (objective is not None) and (previous.objective is not None):
                abs_delta = abs(objective - previous.objective)

            # Calculate relative delta
            if (previous.relative_gap is not None and rel_gap is not None):
                rel_delta = previous.relative_gap - rel_gap

            # Assign to solution
            result.objective       = objective
            result.objective_bound = bound
            result.absolute_gap    = abs_gap
            result.relative_gap    = rel_gap
            result.absolute_delta  = abs_delta 
            result.relative_delta  = rel_delta
            
            # Extract solved variables
            for var in variables:
                value = mz_result[var]
                result.variables[var] = value

            if rel_gap is not None:
                log.debug(f'"{name}" solution {result.iteration} has objective {result.objective} and gap {rel_gap:.2%} after {result.elapsed}')
            elif objective is not None:
                log.debug(f'"{name}" solution {result.iteration} has objective {result.objective} after {result.elapsed}')
            else:
                log.debug(f'"{name}" solution {result.iteration} found after {result.elapsed}')

            for key,value in statistics.items():
                log.debug(f'"{name}" {key} = {value}')
            yield result
            previous = result

    except Exception as e:
        result.error = e.args[0]
        result.status = Status.ERROR
        log.error(f'{type(e).__name__}: {result.error}')

    yield result            
    return


async def best_solution(model : str, options : SolveOptions, **kwargs) -> Result:
    """
    Solve the model, returning only the last (and best) solution.

    For intermediate solutions use the `solutions` function
    """
    result = Result()
    
    async for result in solve(model, options=options, **kwargs):
        pass
    
    return result


async def satisfy(model : str, options : SolveOptions, parameters=None, **kwargs) -> Result:
    """
    Solve the model and return the first satisfactory solution
    """
    kwargs = kwargs | dict(all_solutions=False)
    result = await best_solution(model, options=options, parameters=parameters, **kwargs)
    return result


async def all_solutions(model : str, options : SolveOptions, parameters=None, **kwargs) -> Tuple[List[Result], Result]:
    """
    Solve the model returning all satisfactory solutions
    """
    last_result = Result()
    solutions = []
    kwargs = kwargs | dict(all_solutions=True)
        
    async for result in solve(model, options=options, parameters=parameters, **kwargs):
        solutions.append(result)

    last_result = solutions[-1]
    solutions = solutions[:-1]
    return solutions, last_result


from ..prelude import *
from typing import List, Set, Union, Literal
from textwrap import indent, dedent

TypeInst = Union[Literal['var'], Literal['par']]

TAB = "\t"
NEWLINE = "\n"
VAR = 'var'
PAR = 'par'


def bracket(expr, newline=False, comment=""):
    start = "(\n" if newline else "("
    end = "\n)" if newline else ")"
    result = start + str(expr) + end

    if comment:
        result = f"% {comment}\n" + result
    return result


def let(bindings, body, brack=True):
    s = "let\n{\n"
    s += indent(bindings, TAB)
    s += "\n}\nin\n"
    if brack:
        s += bracket(body, newline=True)
    else:
        s += body
    return s


def and_(*exprs, **kwargs):
    """
    Create an AND expression

    mz_and('1>2', 'x = y')

    "(1 > 2) /\\ (x = y)"
    """
    return join(*exprs, separator="/\\", **kwargs)


def or_(*exprs, **kwargs):
    """
    Create an OR expression

    mz_or('1>2', 'x = y')

    "(1 > 2) \\/ (x = y)"
    """
    return join(*exprs, separator="\\/", **kwargs)


def sum(*exprs, **kwargs):
    """
    Create a SUM expression

    sum('array','xs[1]', '34')
    yields
    "(array + xs[1] + 34)"
    """
    return join(*exprs, separator="+", **kwargs)


def join(*exprs, separator=",", bracket=True, newline=True):
    """
    Join the given expressions with a seperator

    seperator:
        the seperator to use
    bracket:
        should we bracket each subexpression?
    newline:
        split each item by a newline?
    tab:
        indent subexpressions?

    """
    if bracket:
        list = lst(*exprs).map(bracket)
    else:
        list = lst(*exprs)
    
    if not list:
        return None

    if newline:
        separator = NEWLINE + separator + NEWLINE

    body = separator.join(list) + NEWLINE
    return body


def value(x):
    """
    Convert the given argument to a minizinc value
    """    
    
    if hasattr(x, "mz_var"):
        return value(x.mz_var)

    elif isinstance(x, bool):
        return "true" if x else "false"

    elif isinstance(x, int):
        return str(x)

    elif isinstance(x, str):
        return x

    raise ValueError(f"cannot format {x} as a MiniZinc value")


def array(*exprs, comments=None, index=None, newline=False, pad=10):
    """
    Create an ARRAY out of the given expressions

    array(1, 2, 3, newline=True, comments=['a','b','c'], index='N')

    array1d(N, [
        1, # a
        2, # b
        3, # c
    ])

    exprs:
        the expressions that make up the set
    index:
        the index set of the array
    comments:
        an array of comments which will be written next to each member
    newline:
        add a newline after each member?
    """
    
    list = [str(v) for v in flatten(*exprs)]
    members = []
    for i, item in enumerate(list):
        string = str(item)
        if comments:
            comment = comments[i]
            string = string.ljust(pad)
            string += f"% {comment}"

        members.append(string)

    if newline or comments:
        open, close, sep = "[\n", "\n]", "\n, "
    else:
        open, close, sep = "[", "]", ", "

    if index:
        open = f"array1d({index}," + open
        close = close + ")"

    expr = open + sep.join(members) + close
    return expr


def range_(start = 1, end=1):
    start_ = value(start)
    end_   = value(end)
    range  = f"{start_}..{end_}"
    return range


def set_(*exprs, comments=None, newline=False, pad=10):
    """
    Create a SET out of the given expressions
        
    set(1, 2, 3, newline=True, comments=['a','b','c'])

    {
        1, # a
        2, # b
        3, # c
    }

    exprs:
        the expressions that make up the set
    comments:
        an array of comments which will be written next to each member
    newline:
        add a newline after each member?
    """

    list = seq(object, *exprs).map(value)
    members = []
    for i, item in enumerate(list):
        string = str(item)
        if comments:
            comment = comments[i]
            string = string.ljust(pad) + f"% {comment}"

        members.append(string)

    if newline or comments:
        open, close, sep = "{\n", "\n}", "\n, "
    else:
        open, close, sep = "{", "}", ", "

    expr = open + sep.join(members) + close
    return expr


def array2d(arr: List[List], x: str = "int", y: str = "int", comments=None):
    """
    Create a 2D ARRAY out of the given expressions

    array2d([[1,2,3],[2,3,4],[3,4,5]])

    "array2d(int, int, [1,2,3,2,3,4,3,4,5])"

    arr:
        the 2D array to convert
    x:
        the first array dimension
    y:
        the second array dimension

    comments (optional):
        an array that gives comments for each row of the array

    """

    array = f"array2d({x}, {y}, [\n"
    n = len(arr)

    def lines(comments=comments):
        for i, row in enumerate1(arr):

            if isinstance(comments, list):
                comment = comments[i - 1]
                yield f"\t%{comment}"

            line = ",".join(map(value, row))
            if i < n:
                line += ","
            yield "\t" + line

    array += "\n".join(list(lines()))
    array += "\n])"
    return array


def array3d(x):
    return x


def constraint(x):
    text = f"constraint {x}"
    return text


def op(left, right, op):
    return f"{value(left)} {op} {value(right)}"


def eq(left, right):
    return op(left, right, "=")


def leq(left, right):
    return op(left, right, "<=")


def geq(left, right):
    return op(left, right, ">=")


def in_(left, right):
    return op(left, right, "in")


def implies(left, right):
    return op(left, right, "->")


def implied_by(left, right):
    return op(left, right, "<-")


def iff(left, right):
    return op(left, right, "<->")


def text(x):
    return str(x) + NEWLINE
    

def comment(text):
    return text(f"% {text}")


def call(keyword, name, body, **kwargs):
    args = ",".join(f"{k}:{v}" for k, v in kwargs.items())
    expr = f"{keyword} {name}({args}) = "
    expr += NEWLINE
    expr += indent(body, TAB)
    return expr


def function(name, body, **kwargs):
    return call("function", name, body, **kwargs)


def predicate(name, body, **kwargs):
    return call("predicate", name, body, **kwargs)


class ModelBuilder:
    """
    Builder for MiniZinc '.mzn' models
    """

    __WIDTH__ = 80


    def __init__(self, text=""):
        self.string = str(text)


    def add_binop(self, left, right, op, **kwargs):
        return self.add_constraint(
            f"{value(left)} {op} {value(right)}",
            **kwargs
        )


    def add_eq(self, left, right, **kwargs):
        return self.add_binop( left, right, "=", **kwargs)
        

    def add_leq(self, left, right, **kwargs):
        return self.add_binop(left, right, "<=", **kwargs)


    def add_geq(self, left, right, **kwargs):
        return self.add_binop(left, right, ">=", **kwargs)


    def add_in(self, left, right, **kwargs):
        return self.add_binop(left, right, "in", **kwargs)


    def add_false(self, x, **kwargs):
        self.add_eq(x, False, **kwargs)


    def add_true(self, x, **kwargs):
        self.add_eq(x, True, **kwargs)


    def add_multiline_comment(self, x):
        if not x:
            return
        self.add_text(dedent(f"/*\n{x}\n*/"))


    def add_text(self, text):
        self.string += text
        self.string += NEWLINE


    def add_expression(self, text, comment=None, pad=20):
        expr = f"{text};"
        
        if comment:
            expr = f"% {comment}\n{expr}"

        self.add_text(expr)
        return expr


    def add_var(self, type, name, value=None, comment="", inline=True):
        """
        Add a decision variable to the model

        type: str
            the type of var to instantiate
            eg: int, bool, set of int, ROAD
        name: str
            the name of the var
        value: optional[any]:
            value to set the variable as
        inline: bool
            if a value was given, should it be assigned inline?
        return: str
            the variable name
        """
                        
        if value is None:
            self.add_expression(f"var {type}: {name}", comment=comment)
        elif inline:
            self.add_expression(f"var {type}: {name} = {value(value)}", comment=comment)
        else:
            self.add_expression(f"var {type}: {name}", comment=comment)
            self.add_eq(name, value)

        return name


    def add_enum(self, name, value=None, comment=""):
        """
        Add an Enumeration to the model
        """
                
        if value is None:
            self.add_expression(f"enum {name}", comment=comment)
        elif isinstance(value, str):
            self.add_expression(f"enum {name} = {value}", comment=comment)
        else:
            self.add_expression(f"enum {name} = {set(value)}", comment=comment)

        return name


    def add_par(self, type, name, value=None, comment=""):
        """
        Add a parameter to the model
        
        type: str
            the type of par to instantiate
        name: str
            the name of the par
        value: optional[any]:
            initiate the par with a value
        return: str
            the variable name
        """
                        
        if value is None:
            self.add_expression(f"{type}: {name}", comment=comment)
        else:
            self.add_expression(f"{type}: {name} = {value(value)}", comment=comment)

        return name


    def add_array(self, *, index:str, name:str, index2:str='', index3:str='', inst : TypeInst = 'par', type:str, value=None, comment="", inline=True, verbose = False):
        """
        Add an Array to the model
        
        name: str
            the name of the array
        type: str
            type of the values
        index: str
            type of the first index
        index2: str
            type of the second index
        index3: str
            type of the third index
        value: optional[any]:
            initiate the array with a value
        inst: [VAR|PAR]:
            var or par?
        
        return: str
            the variable name
        """
                
        if index3:
            atype = f'array3d({index}, {index2}, {index3}'
            ti = f'array[{index}, {index2}, {index3}]'
        elif index2:
            array = f'array[{index}, {index2}]'
            ti = f'array2d({index}, {index2}'
        else:
            array = f'array[{index}]'
            ti = f'array(index'
            
        root = f'{ti} of {inst} {type}: {name}'
        stem = value
                        
        if (value is not None) and not isinstance(value, str):
            stem = array(value)
            if verbose:
                stem = atype + ',' + stem + ')'
        
        if stem is None:
            self.add_expression(root, comment=comment)
        elif not inline:
            self.add_expression(root, comment=comment)
            self.add_eq(name, stem)
        else:
            self.add_expression(f'{root} = {stem}', comment=comment)

        return name


    def add_global(self, *names):
        """
        Add the the global constraints of the
        given names to the model via 'include'
        statements
        """
        
        for name in names:
            self.add_expression(f'include "{name}.mzn"')


    def add_set(self, *, inst : TypeInst = 'par', name:str, type:str, value=None, min=1, max=None, comment=""):
        """
        Add a Set to the model
                
        type: str
            type of the values
        name: str
            the name of the array
        value: optional[any]:
            initiate the array with a value
        variable : bool:
            var or par?
        return: str
            the variable name
        """
                        
        expr_type = f'{inst} set of {type!s}'

        if max is not None:
            self.add_expression(f"{expr_type}: {name} = {range_(min, max)}", comment=comment)
        elif value is None:
            self.add_expression(f"{expr_type}: {name}", comment=comment)
        elif isinstance(value, str):
            self.add_expression(f"{expr_type}: {name} = {value}", comment=comment)
        else:
            self.add_expression(f"{expr_type}: {name} = {set(value)}", comment=comment)

        return name
        

    def add_constraint(self, expr, /, *, name="", comment=True, pad=20, enabled=True, disabled=False):

        if not expr:
            return

        if disabled:
            return
        
        if not enabled:
            return

        self.add_expression(
            f"constraint {expr}",
            comment=comment and name,
            pad=pad
        )

        return expr


    def add_assign(self, **kwargs):
        """
        Add assignment statements
        """
        for left, right in kwargs.items():
            self.add_expression(f"{left} = {value(right)}")


    def add_implies(self, left, right, **kwargs):
        op = implies(left, right)
        self.add_constraint(op, **kwargs)


    def add_comment(self, text):
        self.add_text(f"% {text}")


    def add_newline(self, x = True):
        if x:
            self.string += NEWLINE


    def add_section(self, title):
        chars = len(str(title))
        right = self.__WIDTH__ - chars - 6
        s = ("=" * 4) + " " + str(title) + " " + ("=" * right)
        self.add_newline()
        self.add_comment(s)
        self.add_newline()


    def __str__(self):
        return self.string


    def __repr__(self):
        return "<MiniZinc Model>"
