"""
Solve the scenario using a the ORTools Python API for
their CP-SAT solver
"""


from unconstrained import *
from .model import *
from ortools.sat.python import cp_model


def solve_with_ortools(scenario : Scenario):
            
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    num_skills = scenario.skills.count
    num_projs  = scenario.projects.count
    num_roles  = scenario.roles.count
    num_staff  = scenario.contributors.count
    max_score = scenario.projects.max('best_score')
    max_day   = scenario.projects.sum('days') + 1

    for p in scenario.projects:
        p._start = model.NewIntVar(0, max_day, f'{p.name} Start')
        p._end = model.NewIntVar(0, max_day, f'{p.name} End')
        p._interval = model.NewIntervalVar(p._start, p.days, p._end, f'{p.name} Interval')
        p._score = model.NewIntVar(0, max_score, f'{p.name} Score')
        
    for r in scenario.roles:
        r._staff = model.NewIntVar(1, num_staff, f'{r.project.name} {r.skill.name} Staff')

    callback = SolutionCallback(scenario)
    solver.Solve(model, callback)
    
    log.info(f'"{scenario.name} - {solver.NumConflicts()} conflicts')
    log.info(f'"{scenario.name} - {solver.NumBranches()} branches')
    log.info(f'"{scenario.name} - {solver.NumBooleans()} booleans')
    log.info(f'"{scenario.name} - {callback.iteration} Solutions')
    log.info(f'"{scenario.name} - {solver.StatusName()}')

    yield True



class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, scenario : Scenario):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.scenario = scenario
        self.iteration = 0

    def on_solution_callback(self):
        self.iteration += 1
        log.debug(f'"{self.scenario.name}" iteration {self.iteration}')

        for p in self.scenario.projects:
            p.start = self.Value(p._start)        
            p.end = self.Value(p._end)
        
        for r in self.scenario.roles:
            r.cont_id = self.Value(r._staff)
            r.staff = self.scenario.contributors.get(r.cont_id)



# array[PROJECT] of var DAY: project_start;
# array[PROJECT] of par DAY: project_duration;
# array[PROJECT] of var DAY: project_end; constraint project_end = [project_start[p] + project_duration[p] | p in PROJECT];
# array[PROJECT] of var DAY: project_late; constraint project_late = [max(project_end[p] - project_end_before[p], 0) | p in PROJECT];
# array[PROJECT] of par DAY: project_end_before;
# array[PROJECT] of par SCORE: project_best_score;
# array[PROJECT] of var SCORE: project_score; constraint project_score = [max(project_best_score[p] - project_late[p], 0) | p in PROJECT];
# array[PROJECT, CONTRIBUTOR] of var bool: project_contributor;


# % ==== Roles =====================================================================

# array[ROLE] of par PROJECT: role_project;

# % Skill required for each role
# array[ROLE] of par SKILL: role_skill;

# % Minimum level required for each role
# array[ROLE] of par LEVEL: role_level;

# % Contributor assigned to each role
# array[ROLE] of var CONTRIBUTOR: role_contributor;

# % Mentor (optional) for each role
# array[ROLE] of var opt CONTRIBUTOR: role_mentor;

# % Did the contributor progress from this role?
# array[ROLE] of var bool: role_progress;

# % ==== Contributors ==============================================================

# array[CONTRIBUTOR, SKILL] of par LEVEL: contributor_skill;
# array[CONTRIBUTOR] of var set of ROLE: contributor_roles;

# % ==== Constraints ===============================================================

# function var LEVEL: get_level(var ROLE: r) =
#     let {
                        
#     var SKILL : s = role_skill[r];
#     var PROJECT: p = role_project[r];
#     var CONTRIBUTOR: c = role_contributor[r];
#     var LEVEL : base = contributor_skill[c, s];
                
#     var LEVEL : progress = 
#         sum (r2 in contributor_roles[c]) (                   
#             % Different role
#             (r != r2)
#             /\\
#             % Same skill
#             (role_skill[r2] = s)
#             /\\
#             % Project Before this
#             (project_end[role_project[r2]] <= project_start[p])
#             /\\
#             % Progressed from role
#             role_progress[r2]
#             )
#             ;
#     }
#     in
#     base + progress
# ;

# % Contributors satisfy the skill requirements for the roles
# constraint forall (r in ROLE) (
#     let {
#         par PROJECT : p    = role_project[r];
#         par SKILL   : s    = role_skill[r];
#         par LEVEL   : l    = role_level[r];
#         var CONTRIBUTOR: c = role_contributor[r];
#     }
#     in
#     % Contributor meets requirements
#     (
#         get_level(r) >= l
#         /\\
#         absent(role_mentor[r])
#     )
#     \\/
#     % Mentor exists
#     (
#         let {
#             var ROLE: r_m;
#             var CONTRIBUTOR: c_m = role_contributor[r_m];
#             var SKILL : s_m = role_skill[r_m];
#         }
#         in
#         r_m != r
#         /\\
#         c_m != c
#         /\\
#         s_m = s
#         /\\
#         get_level(r) = (l - 1)
#         /\\
#         get_level(r_m) >= l
#     )        
# )
# ;

# % Int Set Channel
# constraint int_set_channel(role_contributor, contributor_roles);

# % Contributors can only work on 1 role at a time
# constraint diffn(
#     [project_start[role_project[r]] | r in ROLE],
#     role_contributor,
#     [project_duration[role_project[r]] | r in ROLE],
#     [1 | r in ROLE]
# )
# ;

# solve maximize sum(project_score);
