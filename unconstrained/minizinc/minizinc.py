from ..prelude import *
from typing import AsyncIterator
from datetime import timedelta
from minizinc import Method
from minizinc import Model as MzModel
from minizinc import Result as MzResult
from minizinc import Solver as Solver
from minizinc import Status as MzStatus
from minizinc.CLI.instance import CLIInstance as MzInstance
from minizinc.result import StdStatisticTypes
from typing import TypedDict

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
        
    if isinstance(x, Solver):
        return x

    solver = Solver.lookup(x)

    if not solver:
        raise ValueError(f'Could not parse solver from {x}')

    return solver


def get_installed_solvers(x):
    return []


class SolveStatus(Enum):
    FEASIBLE      = "feasible"
    OPTIMAL       = "optimal"
    THRESHOLD     = "threshold"
    UNSATISFIABLE = "unsatisfiable"
    TIMEOUT       = "timeout"
    ERROR         = "error"
    UNKNOWN       = "unknown"
    UNBOUNDED     = "unbounded"
    
    @property
    def has_solution(self):
        return self in [SolveStatus.FEASIBLE, SolveStatus.OPTIMAL, SolveStatus.THRESHOLD]

    @property
    def is_error(self):        
        return self in [SolveStatus.ERROR, SolveStatus.UNKNOWN, SolveStatus.UNBOUNDED]
    

@attr.s
class MiniZincResult:
    """
    A result provided by MiniZinc
    """
    name             : str             = string_field()
    model_string     : str             = string_field()
    model_file       : str             = string_field()
    method           : Method          = enum_field(Method, SATISFY)
    status           : SolveStatus     = enum_field(SolveStatus, SolveStatus.FEASIBLE)
    error            : str             = string_field()
    compile_time     : Duration        = duration_field()
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
    
    solution : Dict[str, Any] = {}
    
    
    @property
    def solve_time(self):
        return self.end_time - self.start_time

    @property
    def solve_duration(self):
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

    def get_value(self, name, *indices) -> Any:
        """
        Get the solution value for the given name
        and indices

        result.get_value('a')
        result.get_value('an_array', 1)
        result.get_value('a_2d_array', 4, 10)
        """
        
        if name not in self.solution:
            raise KeyError(f'Solution does not contain a value for "{name}"')

        value = self.solution[name]
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
        return f'SolveResult "{self.name}" - {self.status.name}'

    def __repr__(self) -> str:
        return f'<{self!s}>'
    


class FlattenOptions(Enum):
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

    NONE        = 0 # Do not optimiser flattening
    SINGLE_PASS = 1 # Single flattening step (default)
    TWO_PASS    = 2 # Flatten twice to make better flattening decisions for the target
    USE_GECODE  = 3 # Perform root-node-propagation with Gecode (adds –two-pass)
    SHAVE       = 4 # Probe bounds of all variables at the root node (adds –use-gecode)
    SAC         = 5 # Probe values of all variables at the root node (adds –use-gecode)



@attr.s
class MiniZincOptions:
    solver_id       : str           = string_field(default="or-tools")
    threads         : int           = int_field(default=4)
    time_limit      : Duration      = duration_field(default=dict(minutes=1))
    flatten_options : FlattenOptions= enum_field(FlattenOptions, FlattenOptions.SINGLE_PASS)
    free_search     : bool          = bool_field(default=True)
    

async def solve_minizinc_model(
        model_string : str,
        options : MiniZincOptions,
        name    : str = 'model',
        debug_path : Union[Path, str] = '/tmp',
        **parameters
        ) -> AsyncIterator[MiniZincResult]:

    import math
    
    solver = get_solver(options.solver_id)

    # Initial solution
    result = MiniZincResult(name=name)
    
    # Create the MiniZinc Instance
    try:
        instance = MzInstance(solver)
        instance.add_string(model_string)
        for param, value in parameters.items():
            instance[param] = value
                                            
        with instance.files() as files:
            for file in files:
                result.model_string += '\n'
                result.model_string += file.read_text()

        result.method = instance.method
        result.status = SolveStatus.FEASIBLE
        variables = set((instance.output or {}).keys())

        if '_checker' in variables:
            variables.remove('_checker')
        
    # Most likely syntax error
    except Exception as e:
        result.error = e.args[0]
        result.model_string = model_string
        result.status = SolveStatus.ERROR
        instance = None
        variables = set()
        log.error(result.error)

    # Write generate model out for debugging
    model_filename = to_filename(name)
    model_folder = to_directory(debug_path, create=True)
    model_file = model_folder / f'{model_filename}.mzn'
    model_file.write_text(result.model_string)
    result.model_file = str(model_file)
    log.debug(f'"{result.name}" written to {result.model_file}')
        
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
            processes = '-p' in solver.stdFlags and options.threads
        ):

            statistics = previous.statistics.copy()
            statistics.update(mz_result.statistics)
                    
            result = MiniZincResult(
                name            = name,
                iteration       = previous.iteration + 1,
                start_time      = previous.start_time,
                end_time        = now(),
                statistics      = statistics,
                compile_time    = previous.compile_time,
                method          = previous.method,
                model_string    = previous.model_string,
                model_file      = previous.model_file,
                status          = SolveStatus.FEASIBLE,
                objective       = previous.objective,
                objective_bound = previous.objective_bound,
                relative_delta  = previous.relative_delta,
                relative_gap    = previous.relative_gap,
                absolute_delta  = previous.absolute_delta,
                absolute_gap    = previous.absolute_gap,
            )

            if 'flatTime' in statistics:
                flat_time = statistics['flatTime']
                result.compile_time = to_duration(flat_time)

            mz_status = mz_result.status
            result.solution = previous.solution
                                                                        
            # No solution - MiniZinc has terminated
            if mz_result.solution is None:
                
                if mz_status == MzStatus.OPTIMAL_SOLUTION:
                    status = SolveStatus.OPTIMAL

                elif mz_status == MzStatus.UNSATISFIABLE:
                    status = SolveStatus.UNSATISFIABLE

                elif mz_status in [MzStatus.ALL_SOLUTIONS, MzStatus.SATISFIED]:
                    status = SolveStatus.FEASIBLE

                elif mz_status == MzStatus.UNBOUNDED:
                    status = SolveStatus.UNBOUNDED

                elif mz_status == MzStatus.UNKNOWN:
                    if result.solve_duration > options.time_limit:
                        status = SolveStatus.TIMEOUT
                    else:
                        status = SolveStatus.UNKNOWN

                else:
                    status = SolveStatus.ERROR

                result.status = status

                for key,value in statistics.items():
                    log.debug(f'"{name}" {key} = {value}')

                log.log(
                    logging.INFO if status.has_solution else logging.ERROR,
                    f'"{name}" exited with status "{status.name}" after {result.elapsed}'
                )
                break

            # An intermediate solution has been given
            objective : Optional[int]   = None
            bound     : Optional[int]   = None
            abs_gap   : Optional[int]   = None
            rel_gap   : Optional[float] = None
            abs_delta : Optional[int]   = None
            rel_delta : Optional[float] = None

            # Extract objective
            if (objective := statistics.get('objective')) is not None: # type:ignore
                result.objective = int(objective)
                objective = result.objective

            # Extract objective bound
            if (bound := statistics.get('objectiveBound')) is not None: # type:ignore
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
                result.solution[var] = value
                

            if rel_gap is not None:
                log.debug(f'"{name}" solution {result.iteration} has objective {result.objective} and gap {rel_gap:.2%} after {result.elapsed}')
            elif objective is not None:
                log.debug(f'"{name}" solution {result.iteration} has objective {result.objective} after {result.elapsed}')
            else:
                log.debug(f'"{name}" solution {result.iteration} found after {result.elapsed}')
                                                                                                        
            yield result
            previous = result


    except Exception as e:
        result.error = e.args[0]
        result.status = SolveStatus.ERROR
        log.error(result.error)
        
    yield result
    # log.debug(f'"{name}" debug written to {debug_file}')

    return
    


async def best_minizinc_solution(
        model_string : str,
        options      : MiniZincOptions,
        name         : str = 'model',
        **parameters
        ) -> MiniZincResult:
    """
    Solve the model and return the best solution

    Equivalent to running `solve_model` and ignoring
    intermediate solutions
    """
        
    result = MiniZincResult()
            
    async for result in solve_minizinc_model(model_string, name=name, options=options, **parameters):
        pass
    
    return result