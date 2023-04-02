from ..prelude import *
from typing import AsyncIterable, Tuple, List
from datetime import timedelta
from minizinc import Method
from minizinc import Result as MzResult
from minizinc import Solver as Solver
from minizinc import Status as MzStatus
from minizinc import Instance
from minizinc import Driver
from typing import TypedDict
from shutil import copy
from copy import deepcopy
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


@attr.s(**ATTRS)
class Result:
    """
    The result of solving a model
    """
    name             : str             = string_field()
    model_string     : str             = string_field()
    model_file       : str             = string_field()
    data_string      : str             = string_field()
    data_file        : str             = string_field()
    method           : Method          = enum_field(Method, SATISFY)
    status           : Status          = enum_field(Status, Status.FEASIBLE)
    error            : str             = string_field()
    flatten_time     : Duration        = duration_field()
    start_time       : DateTime        = datetime_field()
    end_time         : DateTime        = datetime_field()
    statistics       : Statistics      = dict_field()
    iteration        : int             = int_field()
    objective        : Optional[int]   = int_field(optional=True)
    objective_bound  : Optional[int]   = int_field(optional=True)
    absolute_gap     : Optional[int]   = int_field(optional=True)
    relative_gap     : Optional[float] = float_field(optional=True)
    absolute_delta   : Optional[int]   = int_field(optional=True)
    relative_delta   : Optional[float] = int_field(optional=True)
    variables        : Dict[str, Any]  = attr.ib(factory=dict)
        
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
    


@attr.s(**ATTRS)
class SolveOptions:
    solver_id       : str           = string_field(default="gecode")
    threads         : int           = int_field(default=4)
    time_limit      : Duration      = duration_field(default=dict(minutes=1))
    flatten_options : FlattenOption = enum_field(FlattenOption, FlattenOption.SINGLE_PASS)
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